from django import forms
from .models import Member


class RegistrationForm(forms.ModelForm):
    """Registration form for new members."""

    class Meta:
        model = Member
        fields = ['full_name', 'email', 'phone', 'experience', 'message']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'placeholder': 'Enter your full name',
                'id': 'name',
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'Enter your email',
                'id': 'email',
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'Enter your phone number',
                'id': 'phone',
            }),
            'experience': forms.Select(attrs={
                'id': 'experience',
            }),
            'message': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'What brings you to The 52 Club?',
                'id': 'message',
            }),
        }
        labels = {
            'full_name': 'FULL NAME',
            'email': 'EMAIL',
            'phone': 'PHONE NUMBER',
            'experience': 'STRENGTH / TRAINING EXPERIENCE',
            'message': 'TELL US ABOUT YOURSELF',
        }
