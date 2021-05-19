from django.utils.translation import gettext_lazy as _

from grappelli.dashboard import modules, Dashboard

from discord.constants import SETTINGS_SINGLETON_ID


class CustomIndexDashboard(Dashboard):
    def init_with_context(self, context):
        self.children.append(
            modules.LinkList(
                _("Management"),
                column=1,
                collapsible=False,
                children=[
                    {
                        "title": _("Manage members"),
                        "url": "/discord/discordmember/",
                        "external": False,
                    },
                    {
                        "title": _("View tasks"),
                        "url": "/discord/task/",
                        "external": False,
                    },
                    {
                        "title": _("Settings"),
                        "url": f"/discord/settings/{SETTINGS_SINGLETON_ID}/change/",
                        "external": False,
                    },
                ],
            )
        )

        self.children.append(
            modules.LinkList(
                _("Resources"),
                column=2,
                collapsible=False,
                children=[
                    {
                        "title": _("Website"),
                        "url": "https://www.eco.com/",
                        "external": True,
                        "target": "_blank",
                    },
                    {
                        "title": _("About"),
                        "url": "https://www.eco.com/about",
                        "external": True,
                        "target": "_blank",
                    },
                    {
                        "title": _("Blog"),
                        "url": "https://www.eco.com/blog",
                        "external": True,
                        "target": "_blank",
                    },
                ],
            )
        )

        self.children.append(
            modules.LinkList(
                _("Help"),
                column=2,
                collapsible=False,
                children=[
                    {
                        "title": _("Report a bug"),
                        "url": "mailto:artem.bernatskyy@gmail.com",
                        "external": True,
                    },
                ],
            )
        )
