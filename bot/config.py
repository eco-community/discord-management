import os
from dotenv import load_dotenv
from distutils.util import strtobool

# load env variables
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
# leave empty string if you don't use sentry
SENTRY_API_KEY = os.getenv("SENTRY_API_KEY", "")
LOG_LEVEL = os.getenv("BOT_LOG_LEVEL", "INFO")
# should the bot log to file or to stdout
LOG_TO_FILE = strtobool(os.getenv("BOT_LOG_TO_FILE", "False"))
SYNC_DISCORD_SECONDS = int(os.getenv("BOT_SYNC_DISCORD_SECONDS", 60))
TASKS_SCAN_SECONDS = int(os.getenv("BOT_TASKS_SCAN_SECONDS", 60))
