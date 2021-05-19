from django import forms

from discord.models import DiscordRole


class DiscordRoleForm(forms.Form):
    role = forms.ModelChoiceField(queryset=DiscordRole.objects.all())
