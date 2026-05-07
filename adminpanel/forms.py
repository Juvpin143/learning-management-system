from django import forms
from django.contrib.auth import get_user_model
from lms.models import Message

User = get_user_model()

class MessageForm(forms.ModelForm):
    receiver = forms.ModelChoiceField(
        queryset=User.objects.all(),
        empty_label="-- Select User --",
        widget=forms.Select(attrs={
            "class": "form-select"
        })
    )

    class Meta:
        model = Message
        fields = ("receiver", "subject", "body")

        widgets = {
            "subject": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Subject (optional)"
            }),
            "body": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Write your message here..."
            }),
        }

class SendMessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ("subject", "body")

        widgets = {
            "subject": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Subject (optional)",
                }
            ),
            "body": forms.Textarea(
                attrs={
                    # ✅ body, not message
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Write your message here...",
                }
            ),
        }
