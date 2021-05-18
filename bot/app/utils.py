from dateutil.relativedelta import relativedelta

import sentry_sdk
from discord.ext import commands

from app.constants import EngagementScoreChoices


def use_sentry(client, **sentry_args):
    """
    Use this compatibility library as a bridge between Discord and Sentry.
    Arguments:
        client: The Discord client object (e.g. `discord.AutoShardedClient`).
        sentry_args: Keyword arguments to pass to the Sentry SDK.
    """

    sentry_sdk.init(**sentry_args)

    @client.event
    async def on_error(event, *args, **kwargs):
        """Don't ignore the error, causing Sentry to capture it."""
        raise

    @client.event
    async def on_command_error(msg, error):
        # don't report errors to sentry related to wrong permissions
        if not isinstance(
            error,
            (
                commands.MissingRole,
                commands.MissingAnyRole,
                commands.BadArgument,
                commands.MissingRequiredArgument,
                commands.errors.CommandNotFound,
            ),
        ):
            raise error


def calculate_engagement_score(messages_count: int) -> int:
    if messages_count >= 1 and messages_count < 11:
        return EngagementScoreChoices.ONE
    elif messages_count >= 11 and messages_count < 21:
        return EngagementScoreChoices.TWO
    elif messages_count >= 21 and messages_count < 31:
        return EngagementScoreChoices.THREE
    elif messages_count >= 31 and messages_count < 51:
        return EngagementScoreChoices.FOUR
    elif messages_count >= 51:
        return EngagementScoreChoices.FIVE
    else:
        return EngagementScoreChoices.ZERO


def humanize_readable_datetime(dt1, dt2) -> str:
    """Kudos to https://stackoverflow.com/a/11157649/5751147"""
    attrs = ["years", "months", "days", "hours"]
    delta = relativedelta(dt1, dt2)
    human_readable_attrs = [
        "%d %s" % (getattr(delta, attr), attr if getattr(delta, attr) > 1 else attr[:-1])
        for attr in attrs
        if getattr(delta, attr)
    ]
    return " ".join(human_readable_attrs)
