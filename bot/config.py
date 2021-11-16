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
REDIS_HOST_URL = os.getenv("REDIS_HOST_URL", "redis://localhost:6379/0")
KEEP_MESSAGES_FOR_ANTISPAM_IN_SECONDS = int(os.getenv("KEEP_MESSAGES_FOR_ANTISPAM_IN_SECONDS", 600))
SPAM_RETRIES_UNTIL_MUTE = int(os.getenv("SPAM_RETRIES_UNTIL_MUTE", 2))
_accountant_bot_ids_str = os.getenv("ACCOUNTANT_BOT_IDS", "814589660692349019,880589163110477854")
ACCOUNTANT_BOT_IDS = list(map(int, _accountant_bot_ids_str.split(",")))
PROJECT_NAME = os.getenv("PROJECT_NAME", "")
