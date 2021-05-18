from tortoise import fields
from tortoise.models import Model

from app.constants import EngagementScoreChoices, TaskTypesChoices, TaskStatusChoices


class DiscordRole(Model):
    """Role table"""

    id = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=255)
    position = fields.IntField(default=0)
    created_at = fields.DatetimeField()

    members: fields.ReverseRelation["DiscordMember"]

    class Meta:
        table = "discord_discordrole"
        ordering = ["-position"]

    def __str__(self):
        return self.name


class DiscordMember(Model):
    """Discord member table"""

    id = fields.BigIntField(pk=True)
    bot = fields.BooleanField(default=False)
    avatar_url = fields.CharField(max_length=255)
    name = fields.CharField(max_length=255)
    username = fields.CharField(max_length=255)  # a little bit of db denormalization
    discriminator = fields.CharField(max_length=255)
    engagement_score = fields.IntEnumField(default=0, enum_type=EngagementScoreChoices)  # db denormalization
    messages_count = fields.IntField(default=0)
    age_of_account = fields.CharField(max_length=255)  # a little bit of db denormalization
    nick = fields.CharField(max_length=255, null=True)
    roles = fields.ManyToManyField("app.DiscordRole", related_name="members", through="discord_discordmember_roles")
    pending = fields.BooleanField(default=False)
    premium_since = fields.DatetimeField(null=True)
    raw_status = fields.CharField(max_length=255)
    joined_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField()

    class Meta:
        table = "discord_discordmember"
        ordering = ["created_at"]

    def __str__(self):
        return self.username


class DiscordRoleMember(Model):
    id = fields.BigIntField(pk=True)
    discordmember = fields.ForeignKeyField("app.DiscordMember", related_name="rolemember")
    discordrole = fields.ForeignKeyField("app.DiscordRole", related_name="rolemember")

    members: fields.ManyToManyRelation[DiscordMember]

    class Meta:
        table = "discord_discordmember_roles"
        unique_together = ("discordmember_id", "discordrole_id")

    def __str__(self):
        return self.id


class Task(Model):
    id = fields.BigIntField(pk=True)
    task_type = fields.CharEnumField(enum_type=TaskTypesChoices)
    members_ids = fields.JSONField()
    roles_ids = fields.JSONField(default=list)
    status = fields.CharEnumField(enum_type=TaskStatusChoices, default=TaskStatusChoices.IN_QUEUE)
    error = fields.TextField()

    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "discord_task"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.task_type} - {self.status} ({self.created_at})"
