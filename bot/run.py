import sys
import logging

from discord import Intents, Activity, ActivityType
from tortoise import Tortoise
from discord.ext import commands
from sentry_sdk.integrations.aiohttp import AioHttpIntegration

import config
from constants import SENTRY_ENV_NAME, TORTOISE_ORM
from app.utils import use_sentry


if __name__ == "__main__":
    # initialize bot params
    intents = Intents.default()
    intents.members = True
    activity = Activity(type=ActivityType.watching, name="ECO discord")
    bot = commands.Bot(command_prefix="!butler.", help_command=None, intents=intents, activity=activity)

    # init sentry SDK
    use_sentry(
        bot,
        dsn=config.SENTRY_API_KEY,
        environment=SENTRY_ENV_NAME,
        integrations=[AioHttpIntegration()],
    )

    # setup logger
    file_handler = logging.FileHandler(filename="eco-discord-management.log")
    stdout_handler = logging.StreamHandler(sys.stdout)

    logging.basicConfig(
        level=logging.getLevelName(config.LOG_LEVEL),
        format="%(asctime)s %(levelname)s:%(message)s",
        handlers=[file_handler if config.LOG_TO_FILE else stdout_handler],
    )
    bot.loop.run_until_complete(Tortoise.init(config=TORTOISE_ORM))
    bot.load_extension("app.extensions.sync_discord")
    bot.load_extension("app.extensions.tasks")
    bot.run(config.TOKEN)
