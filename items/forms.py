from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from PIL import Image as PILImage
from .models import Item, RecoveryRequest, ItemReport, SupportTicket



class UserRegisterForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'student@campus.edu or your email'}),
        help_text="Your college or personal email address (used only for account login & notifications, never displayed publicly)."
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a username'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'


class ItemForm(forms.ModelForm):
    MAX_IMAGE_SIZE_MB = 5
    ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']

    class Meta:
        model = Item
        fields = [
            'title',
            'report_type',
            'category',
            'campus_location',
            'date_lost_or_found',
            'image',
            'description',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'e.g. Black Dell Inspiron Laptop Charger, Blue Hydro Flask...'
            }),
            'report_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'campus_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Central Library - 2nd Floor Reading Room or Science Block Canteen'
            }),
            'date_lost_or_found': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/png,image/webp'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Detailed description of the item (color, brand, visible stickers or scratches). DO NOT write sensitive info like full ID numbers, passwords, or home addresses.'
            }),
        }

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if not image or not hasattr(image, 'size'):
            return image

        # File size check
        max_bytes = self.MAX_IMAGE_SIZE_MB * 1024 * 1024
        if image.size > max_bytes:
            raise ValidationError(
                f"Image size cannot exceed {self.MAX_IMAGE_SIZE_MB}MB. Uploaded file is {image.size / (1024*1024):.1f}MB."
            )

        # File extension check
        ext = image.name.split('.')[-1].lower() if '.' in image.name else ''
        if ext not in self.ALLOWED_IMAGE_EXTENSIONS:
            raise ValidationError(
                f"Unsupported image format: .{ext}. Allowed formats: {', '.join(self.ALLOWED_IMAGE_EXTENSIONS).upper()}."
            )

        # Pillow verification: verify image integrity
        try:
            img = PILImage.open(image)
            img.verify()
        except Exception:
            raise ValidationError("The uploaded file is not a valid or readable image.")

        return image

    def clean_date_lost_or_found(self):
        selected_date = self.cleaned_data.get('date_lost_or_found')
        if selected_date:
            today = timezone.now().date()
            if selected_date > today + timedelta(days=1):
                raise ValidationError("The date cannot be in the future.")
        return selected_date


class RecoveryRequestForm(forms.ModelForm):
    class Meta:
        model = RecoveryRequest
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe specific identifying features to prove ownership (e.g. stickers, lock screen wallpaper, brand, exact color, keychain details, or contents). The listing owner will review this claim.'
            }),
        }
        labels = {
            'message': 'Proof of Ownership & Details'
        }


class ItemReportForm(forms.ModelForm):
    class Meta:
        model = ItemReport
        fields = ['reason', 'details']
        widgets = {
            'reason': forms.Select(attrs={'class': 'form-select'}),
            'details': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Please describe why this listing should be reviewed by moderators...'
            }),
        }


class SupportTicketForm(forms.ModelForm):

    class Meta:
        model = SupportTicket
        fields = ['contact_email', 'subject', 'related_error_code', 'priority', 'message']
        widgets = {
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'student@campus.edu'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief summary of issue (e.g. Cannot upload ID photo or Error 404 on item)'
            }),
            'related_error_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 404, 403, 500, CLF-1001 (Optional)'
            }),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Provide full details, steps to reproduce, or questions for our college helpdesk...'
            }),
        }

