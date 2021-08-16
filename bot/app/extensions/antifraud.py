import logging
import asyncio

import discord
from sentry_sdk import capture_exception, Hub
from discord.ext import commands, tasks

import config
from constants import GUILD_INDEX
from app.models import Task
from app.constants import TaskTypesChoices


class AntiFraudCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.anti_fraud_lock = asyncio.Lock()
        self.guild: discord.Guild = None
        self.anti_fraud_task.start()

    def cog_unload(self):
        self.anti_fraud_task.cancel()

    @tasks.loop(seconds=config.TASKS_SCAN_SECONDS)
    async def anti_fraud_task(self):
        with Hub(Hub.current):
            # ensure that only one instance of job is running, other instances will be discarded
            if not self.anti_fraud_lock.locked():
                await self.anti_fraud_lock.acquire()
                try:
                    await self.ban_copycats()
                except Exception as e:
                    logging.debug(f":::discord_management: {e}")
                    capture_exception(e)
                finally:
                    self.anti_fraud_lock.release()

    @anti_fraud_task.before_loop
    async def before_anti_fraud_task(self):
        await self.bot.wait_until_ready()
        if self.guild is None:
            self.guild = self.bot.guilds[GUILD_INDEX]

    async def ban_copycats(self) -> None:
        # ban users impersonating "The Accountant"
        member_ids_to_ban = set()
        # search for impersonators
        for member in self.bot.discord_members:
            is_member_suspected = "accountant" in member.name.lower() or "accountant" in str(member.nick).lower()
            is_member_real_accountant = int(member.id) == int(config.ACCOUNTANT_BOT_ID)
            if is_member_suspected and not is_member_real_accountant:
                member_ids_to_ban.add(member.id)
        # ban impersonators
        member_ids_to_ban_list = list(member_ids_to_ban)
        # prevent duplicate ban tasks
        if member_ids_to_ban_list and not await Task.exists(
            members_ids=member_ids_to_ban_list, task_type=TaskTypesChoices.BAN
        ):
            await Task.create(members_ids=member_ids_to_ban_list, task_type=TaskTypesChoices.BAN)
        return None


def setup(bot):
    bot.add_cog(AntiFraudCog(bot))
