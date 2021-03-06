import logging
import asyncio

import discord
from sentry_sdk import capture_exception, Hub
from discord.ext import commands, tasks

import config
from constants import GUILD_INDEX
from app.models import Task, Settings
from app.constants import TaskStatusChoices, TaskTypesChoices, SETTINGS_SINGLETON_ID


class TasksCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.lock = asyncio.Lock()
        self.guild: discord.Guild
        self.execute_tasks_job.start()

    def cog_unload(self):
        self.execute_tasks_job.cancel()

    @tasks.loop(seconds=config.TASKS_SCAN_SECONDS)
    async def execute_tasks_job(self):
        with Hub(Hub.current):
            # ensure that only one instance of job is running, other instances will be discarded
            if not self.lock.locked():
                await self.lock.acquire()
                try:
                    await self.execute_tasks()
                except Exception as e:
                    logging.debug(f":::discord_management: {e}")
                    capture_exception(e)
                finally:
                    self.lock.release()

    @execute_tasks_job.before_loop
    async def before_execute_tasks_job(self):
        await self.bot.wait_until_ready()
        self.guild = self.bot.guilds[GUILD_INDEX]

    async def execute_tasks(self) -> None:
        tasks = await Task.filter(status=TaskStatusChoices.IN_QUEUE)
        settings, _ = await Settings.get_or_create(id=SETTINGS_SINGLETON_ID)
        for task in tasks:
            try:
                # set task status to "started"
                task.status = TaskStatusChoices.STARTED
                await task.save(update_fields=["status", "modified_at"])
                for member_id in task.members_ids:
                    try:
                        member = self.guild.get_member(member_id)
                        if not member:
                            member = await self.guild.fetch_member(member_id)
                        if task.task_type == TaskTypesChoices.KICK:
                            await self.guild.kick(user=member, reason="Discord_Management")
                        elif task.task_type == TaskTypesChoices.ASSIGN_ROLE:
                            roles = [self.guild.get_role(_) for _ in task.roles_ids]
                            await member.add_roles(*roles, reason="Discord_Management")
                        elif task.task_type == TaskTypesChoices.REMOVE_ROLE:
                            roles = [self.guild.get_role(_) for _ in task.roles_ids]
                            await member.remove_roles(*roles, reason="Discord_Management")
                        elif task.task_type == TaskTypesChoices.BAN:
                            await self.guild.ban(
                                user=member,
                                reason="Discord_Management",
                                delete_message_days=settings.delete_message_days_when_banned,
                            )
                    except discord.errors.NotFound:
                        pass  # ignore errors related to not found members
                # set task status to "finished"
                task.status = TaskStatusChoices.FINISHED
                await task.save(update_fields=["status", "modified_at"])
            except Exception as e:
                task.error = str(e)
                task.status = TaskStatusChoices.FAILED
                await task.save(update_fields=["error", "status", "modified_at"])
                capture_exception(e)


def setup(bot):
    bot.add_cog(TasksCog(bot))
