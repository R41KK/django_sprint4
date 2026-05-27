from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Comment, Post

User = get_user_model()


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("title", "text", "pub_date", "location", "category", "image")
        widgets = {
            "pub_date": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")
