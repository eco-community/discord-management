from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


class Settings(models.Model):
    """Settings singleton table"""

    delete_message_days_when_banned = models.IntegerField(
        default=1, validators=[MinValueValidator(0), MaxValueValidator(7)]
    )

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "settings"
        verbose_name_plural = "settings"

    def __str__(self):
        return str(self.pk)


class DiscordRole(models.Model):
    """Discord role table"""

    id = models.BigIntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    position = models.IntegerField(default=0)
    created_at = models.DateTimeField()

    class Meta:
        ordering = ["-position"]

    def __str__(self):
        return self.name


class DiscordMember(models.Model):
    """Discord member table"""

    class EngagementScoreChoices(models.IntegerChoices):
        ZERO = 0, "0"
        ONE = 1, "1"
        TWO = 2, "2"
        THREE = 3, "3"
        FOUR = 4, "4"
        FIVE = 5, "5"

    id = models.BigIntegerField(primary_key=True)
    bot = models.BooleanField(default=False)
    avatar_url = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    username = models.CharField(max_length=255)  # a little bit of db denormalization
    discriminator = models.CharField(max_length=255)
    engagement_score = models.IntegerField(default=0, choices=EngagementScoreChoices.choices)  # db denormalization
    messages_count = models.IntegerField(default=0)
    age_of_account = models.CharField(max_length=255)  # a little bit of db denormalization
    nick = models.CharField(max_length=255, blank=True, null=True)
    roles = models.ManyToManyField(DiscordRole, related_name="members", blank=True)
    pending = models.BooleanField(default=False)
    premium_since = models.DateTimeField(blank=True, null=True)
    joined_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return self.username


class Task(models.Model):
    """Task table"""

    class TaskTypesChoices(models.TextChoices):
        KICK = "KICK"  # Kick members
        BAN = "BAN"  # Ban members
        ASSIGN_ROLE = "ASSIGN_ROLE"  # Assign role to members
        REMOVE_ROLE = "REMOVE_ROLE"  # Remove role from members

    class TaskStatusChoices(models.TextChoices):
        IN_QUEUE = "IN_QUEUE"  # Task in queue
        STARTED = "STARTED"  # Task started
        FINISHED = "FINISHED"  # Task finished
        FAILED = "FAILED"  # Task failed

    task_type = models.CharField(choices=TaskTypesChoices.choices, max_length=255)
    members_ids = models.JSONField()  # list of members ids
    roles_ids = models.JSONField(default=list, blank=True)  # list of roles ids
    status = models.CharField(default=TaskStatusChoices.IN_QUEUE, choices=TaskStatusChoices.choices, max_length=255)
    error = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.task_type} - {self.status} ({self.created_at})"
