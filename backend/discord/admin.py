import csv
from io import StringIO

from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.shortcuts import render
from django.http import HttpResponseRedirect, StreamingHttpResponse
from django.utils.safestring import mark_safe
from django.template.defaultfilters import pluralize

from discord.forms import DiscordRoleForm
from discord.models import DiscordMember, Task, Settings
from discord.constants import SETTINGS_SINGLETON_ID

from .utils import keyset_pagination_iterator


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # ensure that singleton exists
        qs.get_or_create(id=SETTINGS_SINGLETON_ID)
        return qs

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DiscordMember)
class DiscordMemberAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("roles")

    fields = [
        "id",
        "avatar",
        "username",
        "roles",
        "nick",
        "bot",
        "pending",
        "engagement_score",
        "messages_count",
        "premium_since",
        "joined_at",
        "created_at",
        "age_of_account",
    ]
    filter_horizontal = ["roles"]
    readonly_fields = ["avatar"]
    list_display = [
        "username",
        "role",
        "engagement_score",
        "messages_count",
        "joined_at",
        "created_at",
        "age_of_account",
    ]
    ordering = ["joined_at"]
    sortable_by = ["username", "bot", "engagement_score", "messages_count", "joined_at", "created_at"]
    list_filter = ["roles", "engagement_score", "joined_at", "created_at", "pending", "bot"]
    search_fields = ["name", "discriminator", "nick", "username"]

    def role(self, obj):
        return ", ".join([_.name for _ in obj.roles.all()])

    @admin.display()
    def avatar(self, obj):
        return format_html(f'<img src="{obj.avatar_url}" width="150" height="150" style="object-fit:contain" />')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    actions = ["kick_action", "ban_action", "assign_role_action", "remove_role_action", "export_as_csv"]

    @admin.action(description="Export selected rows to CSV")
    def export_as_csv(self, request, queryset):
        def rows(queryset):

            csvfile = StringIO()
            csvwriter = csv.writer(csvfile)
            columns = [field.name for field in self.model._meta.fields]

            def read_and_flush():
                csvfile.seek(0)
                data = csvfile.read()
                csvfile.seek(0)
                csvfile.truncate()
                return data

            header = False

            if not header:
                header = True
                csvwriter.writerow(columns)
                yield read_and_flush()

            for row in keyset_pagination_iterator(queryset):
                csvwriter.writerow(getattr(row, column) for column in columns)
                yield read_and_flush()

        response = StreamingHttpResponse(rows(queryset), content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=%s.csv" % self.model.__name__
        return response

    @admin.action(description="Kick members from Discord")
    def kick_action(self, request, queryset):
        members_ids = list(queryset.values_list("id", flat=True))
        task = Task.objects.create(members_ids=members_ids, task_type=Task.TaskTypesChoices.KICK)
        members_count = queryset.count()
        self.message_user(
            request,
            mark_safe(
                f"{members_count} member{pluralize(members_count)} will be kickeded shortly, <a href='/discord/task/{task.id}/change/'>track progress here</a>"  # noqa: E501
            ),
            level=messages.SUCCESS,
        )

    @admin.action(description="Ban members from Discord")
    def ban_action(self, request, queryset):
        members_ids = list(queryset.values_list("id", flat=True))
        task = Task.objects.create(members_ids=members_ids, task_type=Task.TaskTypesChoices.BAN)
        members_count = queryset.count()
        self.message_user(
            request,
            mark_safe(
                f"{members_count} member{pluralize(members_count)} will be banned shortly, <a href='/discord/task/{task.id}/change/'>track progress here</a>"  # noqa: E501
            ),
            level=messages.SUCCESS,
        )

    @admin.action(description="Assign role to members")
    def assign_role_action(self, request, queryset):
        do_select_across = "select_across" in request.POST and request.POST["select_across"] == "1"
        members_count = queryset.count()
        if "do_assign_role_action" in request.POST:
            form = DiscordRoleForm(request.POST)
            if form.is_valid():
                role = form.cleaned_data["role"]
                task = Task.objects.create(
                    task_type=Task.TaskTypesChoices.ASSIGN_ROLE,
                    members_ids=list(queryset.values_list("id", flat=True)),
                    roles_ids=[role.id],
                )
                self.message_user(
                    request,
                    mark_safe(
                        f"{role.name} role will be assigned shortly to {members_count} member{pluralize(members_count)}, <a href='/discord/task/{task.id}/change/'>track progress here</a>"  # noqa: E501
                    ),
                    level=messages.SUCCESS,
                )
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = DiscordRoleForm()
        return render(
            request,
            "admin/manage_role_intermediate.html",
            context={
                "action_name": "assign",
                "objects": queryset if not do_select_across else queryset[:100],
                "form": form,
                "select_across": "0" if not do_select_across else "1",
                "members_count": members_count,
            },
        )

    @admin.action(description="Remove role from members")
    def remove_role_action(self, request, queryset):
        do_select_across = "select_across" in request.POST and request.POST["select_across"] == "1"
        members_count = queryset.count()
        if "do_remove_role_action" in request.POST:
            form = DiscordRoleForm(request.POST)
            if form.is_valid():
                role = form.cleaned_data["role"]
                task = Task.objects.create(
                    task_type=Task.TaskTypesChoices.REMOVE_ROLE,
                    members_ids=list(queryset.values_list("id", flat=True)),
                    roles_ids=[role.id],
                )
                self.message_user(
                    request,
                    mark_safe(
                        f"{role.name} role will be removed shortly from {members_count} member{pluralize(members_count)}, <a href='/discord/task/{task.id}/change/'>track progress here</a>"  # noqa: E501
                    ),
                    level=messages.SUCCESS,
                )
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = DiscordRoleForm()
        return render(
            request,
            "admin/manage_role_intermediate.html",
            context={
                "action_name": "remove",
                "objects": queryset if not do_select_across else queryset[:100],
                "form": form,
                "select_across": "0" if not do_select_across else "1",
                "members_count": members_count,
            },
        )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["__str__", "created_at"]
    list_filter = ["status", "task_type"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
