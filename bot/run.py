import sys
import logging

from discord import Intents, Activity, ActivityType
from tortoise import Tortoise
from discord.ext import commands

import config
from constants import SENTRY_ENV_NAME, TORTOISE_ORM
from app.utils import use_sentry


if __name__ == "__main__":
    # initialize bot params
    intents = Intents.default()
    intents.members = True
    intents.messages = True
    activity = Activity(type=ActivityType.watching, name=f"{config.PROJECT_NAME} discord".upper())
    bot = commands.Bot(command_prefix="!butler.", help_command=None, intents=intents, activity=activity)

    # init sentry SDK
    use_sentry(
        bot,
        dsn=config.SENTRY_API_KEY,
        environment=SENTRY_ENV_NAME,
        integrations=[],
    )

    # setup logger
    file_handler = logging.FileHandler(filename="discord-management.log")
    stdout_handler = logging.StreamHandler(sys.stdout)

    logging.basicConfig(
        level=logging.getLevelName(config.LOG_LEVEL),
        format="%(asctime)s %(levelname)s:%(message)s",
        handlers=[file_handler if config.LOG_TO_FILE else stdout_handler],
    )
    bot.loop.run_until_complete(Tortoise.init(config=TORTOISE_ORM))
    bot.load_extension("app.extensions.sync_discord")
    bot.load_extension("app.extensions.tasks")
    bot.load_extension("app.extensions.antifraud")
    bot.run(config.TOKEN)
