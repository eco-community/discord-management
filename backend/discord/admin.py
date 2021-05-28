from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from django.shortcuts import render
from django.http import HttpResponseRedirect

from discord.forms import DiscordRoleForm
from discord.models import DiscordMember, Task, Settings
from discord.constants import SETTINGS_SINGLETON_ID


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

    actions = ["kick_action", "ban_action", "assign_role_action", "remove_role_action"]

    @admin.action(description="Kick members from Discord")
    def kick_action(self, request, queryset):
        members_ids = list(queryset.values_list("id", flat=True))
        Task.objects.create(members_ids=members_ids, task_type=Task.TaskTypesChoices.KICK)
        self.message_user(request, "Selected users will be kicked from Discord server", level=messages.SUCCESS)

    @admin.action(description="Ban members from Discord")
    def ban_action(self, request, queryset):
        members_ids = list(queryset.values_list("id", flat=True))
        Task.objects.create(members_ids=members_ids, task_type=Task.TaskTypesChoices.BAN)
        self.message_user(request, "Selected users will be banned from Discord server", level=messages.SUCCESS)

    @admin.action(description="Assign role to members")
    def assign_role_action(self, request, queryset):
        if "do_assign_role_action" in request.POST:
            form = DiscordRoleForm(request.POST)
            if form.is_valid():
                role = form.cleaned_data["role"]
                Task.objects.create(
                    task_type=Task.TaskTypesChoices.ASSIGN_ROLE,
                    members_ids=list(queryset.values_list("id", flat=True)),
                    roles_ids=[role.id],
                )
                self.message_user(
                    request,
                    f"{role.name} role will be assigned to {queryset.count()} members",
                    level=messages.SUCCESS,
                )
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = DiscordRoleForm()
        return render(
            request,
            "admin/manage_role_intermediate.html",
            context={"action_name": "assign", "objects": queryset, "form": form},
        )

    @admin.action(description="Remove role from members")
    def remove_role_action(self, request, queryset):
        if "do_remove_role_action" in request.POST:
            form = DiscordRoleForm(request.POST)
            if form.is_valid():
                role = form.cleaned_data["role"]
                Task.objects.create(
                    task_type=Task.TaskTypesChoices.REMOVE_ROLE,
                    members_ids=list(queryset.values_list("id", flat=True)),
                    roles_ids=[role.id],
                )
                self.message_user(
                    request,
                    f"{role.name} role will be removed from {queryset.count()} members",
                    level=messages.SUCCESS,
                )
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = DiscordRoleForm()
        return render(
            request,
            "admin/manage_role_intermediate.html",
            context={"action_name": "remove", "objects": queryset, "form": form},
        )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["__str__", "created_at"]
    list_filter = ["status", "task_type"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
