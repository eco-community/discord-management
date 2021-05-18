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


class SyncDiscord(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.lock = asyncio.Lock()
        self.guild: discord.Guild
        self.members: List[discord.Member]
        self.members_messages_count: Dict[int, int] = defaultdict(lambda: 0, {})  # id, messages_count
        self.roles: List[discord.Role]
        self.sync_discord_to_db.start()

    def cog_unload(self):
        self.sync_discord_to_db.cancel()

    @tasks.loop(seconds=config.SYNC_DISCORD_SECONDS)
    async def sync_discord_to_db(self):
        with Hub(Hub.current):
            # ensure that only one instance of job is running, other instances will be discarded
            if not self.lock.locked():
                await self.lock.acquire()
                try:
                    async with in_transaction():
                        await self.sync_roles()
                        await self.calculate_messages_count()
                        await self.sync_members()
                        await self.sync_member_roles()
                except Exception as e:
                    logging.debug(f":::discord_management: {e}")
                    capture_exception(e)
                finally:
                    self.lock.release()

    @sync_discord_to_db.before_loop
    async def before_sync_discord_to_db(self):
        await self.bot.wait_until_ready()
        self.guild = self.bot.guilds[GUILD_INDEX]

    async def sync_roles(self) -> None:
        # refresh roles cache
        await self.fetch_all_roles()
        # remove all old discord roles, because we don't have any other solution how to detect updates
        # because we execute this in single transaction it should be fine
        await DiscordRole.all().delete()
        await DiscordRole.bulk_create(
            [
                DiscordRole(
                    id=_.id,
                    name=_.name,
                    position=_.position,
                    created_at=_.created_at,
                )
                for _ in self.roles
            ]
        )

    async def sync_members(self) -> None:
        # refresh members cache
        await self.fetch_all_members()
        # remove all old discord members, because we don't have any other solution how to detect updates
        # because we execute this in single transaction it should be fine
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
                    raw_status=_.raw_status,
                    joined_at=_.joined_at,
                    created_at=_.created_at,
                )
                for _ in self.members
            ]
        )

    async def sync_member_roles(self) -> None:
        # remove all old DiscordRoleMember, because we don't have any other solution how to detect updates
        # because we execute this in single transaction it should be fine
        await DiscordRoleMember.all().delete()
        bulk_create_list = []
        for member in self.members:
            for role in member.roles:
                bulk_create_list.append(
                    DiscordRoleMember(
                        discordmember_id=member.id,
                        discordrole_id=role.id,
                    )
                )
        await DiscordRoleMember.bulk_create(bulk_create_list)

    async def calculate_messages_count(self) -> None:
        self.members_messages_count.clear()
        for channel in self.guild.channels:
            if hasattr(channel, "history"):
                async for message in channel.history(limit=None):
                    self.members_messages_count[message.author.id] += 1

    async def fetch_all_members(self) -> None:
        """Get fresh list of up-to-date members"""
        self.members = []
        async for member in self.guild.fetch_members(limit=None):
            self.members.append(member)

    async def fetch_all_roles(self) -> None:
        """Get fresh list of up-to-date roles"""
        self.roles = await self.guild.fetch_roles()


def setup(bot):
    bot.add_cog(SyncDiscord(bot))
