from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html

from discord.models import DiscordMember, Task


@admin.register(DiscordMember)
class DiscordMemberAdmin(admin.ModelAdmin):
    fields = [
        "id",
        "avatar",
        "username",
        "roles",
        "raw_status",
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
    list_display = ["username", "bot", "engagement_score", "joined_at", "created_at", "age_of_account"]
    sortable_by = ["username", "bot", "engagement_score", "joined_at", "created_at"]
    list_filter = ["roles", "bot", "engagement_score", "joined_at", "pending"]
    search_fields = ["name", "discriminator", "nick", "username"]

    @admin.display()
    def avatar(self, obj):
        return format_html(f'<img src="{obj.avatar_url}" width="150" height="150" style="object-fit:contain" />')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    actions = ["kick", "ban"]

    @admin.action(description="Kick selected members from Discord")
    def kick(self, request, queryset):
        members_ids = list(queryset.values_list("id", flat=True))
        Task.objects.create(members_ids=members_ids, task_type=Task.TaskTypesChoices.KICK)
        self.message_user(request, "Selected users will be kicked from Discord server", level=messages.SUCCESS)

    @admin.action(description="Ban selected members from Discord")
    def ban(self, request, queryset):
        members_ids = list(queryset.values_list("id", flat=True))
        Task.objects.create(members_ids=members_ids, task_type=Task.TaskTypesChoices.BAN)
        self.message_user(request, "Selected users will be banned from Discord server", level=messages.SUCCESS)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(status=Task.TaskStatusChoices.IN_QUEUE)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
