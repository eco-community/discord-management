import re
from typing import List
from datetime import timedelta, datetime

import discord
import aioredis
from dateutil import parser
from discord.ext import commands

import config
from app.constants import MUTED_ROLE, CACHE_INDEX, CACHE_PREFIX, CACHE_SEPARATOR, ADMIN_ROLE


class SpamItem:
    """Class for keeping parsed data for cached messages"""

    def __init__(self, cache_id=None, message_id=None, channel_id=None):
        if cache_id:
            self.cache_id = cache_id
            # unpack and convert to int
            self.message_id, self.channel_id = map(
                int, self.cache_id.decode().split(CACHE_PREFIX)[1].split(CACHE_SEPARATOR)
            )
        else:
            self.message_id, self.channel_id = int(message_id), int(channel_id)
            self.cache_id = f"{CACHE_PREFIX}{self.message_id}{CACHE_SEPARATOR}{self.channel_id}"

    def to_json(self):
        return self.cache_id

    def to_discord(self):
        return discord.Object(id=self.message_id)


class AntiSpamCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        self.bot.loop.create_task(self.ensure_redisearch_index_exists())

    async def ensure_redisearch_index_exists(self) -> None:
        try:
            # we will disable stop words and stemming because for now we will do exact search using list of tokens
            await self.bot.redis_client.execute_command(
                f"FT.CREATE idx:{CACHE_INDEX} ON hash PREFIX 1 {CACHE_PREFIX} STOPWORDS 0 SCHEMA content TEXT NOSTEM author_id TAG"  # noqa: E501
            )
        except aioredis.exceptions.ResponseError as e:
            assert str(e) == "Index already exists", "Ensure that error is due to index already existing"
        return None

    def tokenize(self, text) -> str:
        return " ".join(re.findall(r"\w+", text))

    async def check_for_spam_items(self, message) -> List[SpamItem]:
        # ignore "spam" from admins
        if discord.utils.get(message.author.roles, name=ADMIN_ROLE):
            return []
        result = await self.bot.redis_client.execute_command(
            "FT.SEARCH",
            f"idx:{CACHE_INDEX}",
            f"@content:'{self.tokenize(message.system_content)}' @author_id:{{{message.author.id}}}",
            "NOCONTENT",
        )
        if len(result) >= 1 and result[0] > 0:  # if query has result
            # convert [2, b'message:856912680-856561546', b'message:85631-85632546'] to [SpamItem, SpamItem]
            spam_items = [SpamItem(_) for _ in result[1:]]
            # append current spam message to spam items retrieved from cache
            spam_items.append(SpamItem(message_id=message.id, channel_id=message.channel.id))
            return spam_items
        else:
            return []

    async def save_message_to_cache(self, message, set_expire=True) -> None:
        await self.bot.redis_client.hset(
            name=f"{CACHE_PREFIX}{message.id}{CACHE_SEPARATOR}{message.channel.id}",
            mapping={
                "content": self.tokenize(message.system_content),
                "author_id": message.author.id,
            },
        )
        if set_expire:
            await self.bot.redis_client.expire(
                name=f"{CACHE_PREFIX}{message.id}{CACHE_SEPARATOR}{message.channel.id}",
                time=config.KEEP_MESSAGES_FOR_ANTISPAM_IN_SECONDS,
            )
        return None

    async def send_dm_message(self, user: discord.User, text: str) -> None:
        try:
            await user.send(text)
        except discord.errors.Forbidden:
            pass  # ignore errors from users that forbid private messages

    async def process_message(self, message, set_expire=True) -> None:
        spam_items = await self.check_for_spam_items(message)
        is_spam = len(spam_items) > config.SPAM_RETRIES_UNTIL_MUTE
        should_warn_user = len(spam_items) > 1 and len(spam_items) <= config.SPAM_RETRIES_UNTIL_MUTE

        if not should_warn_user and not is_spam:  # handle ordinary message
            await self.save_message_to_cache(message, set_expire=set_expire)
        elif should_warn_user:  # warn user not to spam
            await self.save_message_to_cache(message, set_expire=set_expire)
            await self.send_dm_message(user=message.author, text="Please don't spam or you will be muted.")
        elif is_spam:  # handle spam message
            muted_role = discord.utils.get(message.guild.roles, name=MUTED_ROLE)
            await message.author.add_roles(muted_role, reason="Discord_Management")
            # remove spam messages
            for spam_item in spam_items:
                channel = self.bot.get_channel(spam_item.channel_id)
                try:
                    await channel.delete_messages([spam_item.to_discord()])
                except discord.errors.NotFound:
                    pass  # ignore race conditions when removing messages
            # clear deleted messages from cache
            await self.bot.redis_client.delete(*[_.to_json() for _ in spam_items])
            # tell user that they were muted
            await self.send_dm_message(user=message.author, text="You were muted for spam, have a nice day.")
        return None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # ignore messages from DM
        if not message.guild:
            return None
        await self.process_message(message)
        return None

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent) -> None:
        # ignore messages from DM
        if not payload.guild_id:
            return None
        # ignore too old messages
        created_at = parser.parse(payload.data["timestamp"], ignoretz=True)
        cached_window_date = datetime.utcnow() - timedelta(seconds=config.KEEP_MESSAGES_FOR_ANTISPAM_IN_SECONDS)
        if created_at > cached_window_date:
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            await self.process_message(message, set_expire=False)
        return None

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        # ignore messages from DM
        if not message.guild:
            return None
        # clear deleted messages from cache
        if message.created_at > datetime.utcnow() - timedelta(seconds=config.KEEP_MESSAGES_FOR_ANTISPAM_IN_SECONDS):
            await self.bot.redis_client.delete(SpamItem(message_id=message.id, channel_id=message.channel.id).cache_id)
        return None


def setup(bot):
    bot.add_cog(AntiSpamCog(bot))
