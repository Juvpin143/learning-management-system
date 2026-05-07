from django import forms
from .models import Course, Profile, Review


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'title',
            'subtitle',
            'description',
            'category',
            'thumbnail',
            'level',
            'promo_video_url',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter course title'
            }),
            'subtitle': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter course subtitle (optional)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Write a description of the course'
            }),
            'category': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter category'
            }),
            'level': forms.Select(attrs={
                'class': 'form-select'
            }),
            'promo_video_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter promo video URL (optional)'
            }),
            'thumbnail': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            'profile_image',
            'full_name',
            'address',
            'phone_number',
            'skills',
            'bio'
        ]

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']


