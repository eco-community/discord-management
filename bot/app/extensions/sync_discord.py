import logging
import asyncio
from collections import defaultdict
from typing import List, Dict
from datetime import datetime


import discord
from sentry_sdk import capture_exception, Hub
from tortoise.transactions import in_transaction
from discord.ext import commands, tasks

import config
from constants import GUILD_INDEX
from app.utils import calculate_engagement_score, humanize_readable_datetime
from app.models import DiscordMember, DiscordRole, DiscordRoleMember
from app.constants import EVERYONE_ROLE


class SyncDiscord(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.sync_users_and_roles_lock = asyncio.Lock()
        self.sync_message_data_lock = asyncio.Lock()
        self.guild: discord.Guild = None
        self.members: List[discord.Member]
        self.members_messages_count: Dict[int, int] = defaultdict(lambda: 0, {})  # id, messages_count
        self.roles: List[discord.Role]
        self.sync_users_and_roles_to_db.start()
        self.sync_message_data_to_db.start()

    def cog_unload(self):
        self.sync_users_and_roles_to_db.cancel()
        self.sync_message_data_to_db.cancel()

    @tasks.loop(seconds=config.SYNC_DISCORD_SECONDS)
    async def sync_users_and_roles_to_db(self):
        with Hub(Hub.current):
            # ensure that only one instance of job is running, other instances will be discarded
            if not self.sync_users_and_roles_lock.locked():
                await self.sync_users_and_roles_lock.acquire()
                try:
                    await self.fetch_users_and_roles()
                    await self.save_users_and_roles_to_db()
                except Exception as e:
                    logging.debug(f":::discord_management: {e}")
                    capture_exception(e)
                finally:
                    self.sync_users_and_roles_lock.release()

    @sync_users_and_roles_to_db.before_loop
    async def before_sync_users_and_roles_to_db(self):
        await self.bot.wait_until_ready()
        if self.guild is None:
            self.guild = self.bot.guilds[GUILD_INDEX]

    @tasks.loop(seconds=config.SYNC_DISCORD_SECONDS)
    async def sync_message_data_to_db(self):
        """Note: because it takes a lot of time we will use a separate task for fetching & analyzing messages"""
        with Hub(Hub.current):
            # ensure that only one instance of job is running, other instances will be discarded
            if not self.sync_message_data_lock.locked():
                await self.sync_message_data_lock.acquire()
                try:
                    await self.fetch_message_data()
                except Exception as e:
                    logging.debug(f":::discord_management: {e}")
                    capture_exception(e)
                finally:
                    self.sync_message_data_lock.release()

    @sync_message_data_to_db.before_loop
    async def before_sync_message_data_to_db(self):
        await self.bot.wait_until_ready()
        if self.guild is None:
            self.guild = self.bot.guilds[GUILD_INDEX]

    async def fetch_message_data(self) -> None:
        # calculate messages count
        _members_messages_count: Dict[int, int] = defaultdict(lambda: 0, {})
        for channel in self.guild.channels:
            try:
                if hasattr(channel, "history") and channel.type is discord.ChannelType.text:
                    async for message in channel.history(limit=None):
                        _members_messages_count[message.author.id] += 1
            except discord.Forbidden:
                pass  # silently ignore private channels
        # switch between cached and fresh message data
        self.members_messages_count = _members_messages_count
        return None

    async def fetch_users_and_roles(self) -> None:
        # fetch all roles
        self.roles = await self.guild.fetch_roles()
        # fetch all members
        self.members = []
        async for member in self.guild.fetch_members(limit=None):
            self.members.append(member)
        return None

    async def save_users_and_roles_to_db(self) -> None:
        async with in_transaction():
            # sync roles
            await DiscordRole.all().delete()
            await DiscordRole.bulk_create(
                [
                    DiscordRole(
                        id=_.id,
                        name=_.name,
                        position=_.position,
                        created_at=_.created_at,
                    )
                    for _ in self.roles if _.name != EVERYONE_ROLE
                ]
            )
            # sync members
            await DiscordRoleMember.all().delete()
            await DiscordMember.all().delete()
            await DiscordMember.bulk_create(
                [
                    DiscordMember(
                        id=_.id,
                        bot=_.bot,
                        avatar_url=_.avatar_url,
                        name=_.name,
                        username=f"{_.name}#{_.discriminator}",
                        discriminator=_.discriminator,
                        engagement_score=calculate_engagement_score(self.members_messages_count[_.id]),
                        messages_count=self.members_messages_count[_.id],
                        age_of_account=humanize_readable_datetime(datetime.now(), _.created_at),
                        nick=_.nick,
                        pending=_.pending,
                        premium_since=_.premium_since,
                        joined_at=_.joined_at,
                        created_at=_.created_at,
                    )
                    for _ in self.members
                ]
            )
            # sync member roles
            bulk_create_list = []
            for member in self.members:
                for role in member.roles:
                    if role.name != EVERYONE_ROLE:
                        bulk_create_list.append(
                            DiscordRoleMember(
                                discordmember_id=member.id,
                                discordrole_id=role.id,
                            )
                        )
            await DiscordRoleMember.bulk_create(bulk_create_list)
        return None


def setup(bot):
    bot.add_cog(SyncDiscord(bot))
