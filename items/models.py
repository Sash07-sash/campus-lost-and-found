from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone


class Item(models.Model):
    REPORT_TYPE_CHOICES = [
        ('LOST', 'Lost Item'),
        ('FOUND', 'Found Item'),
    ]

    CATEGORY_CHOICES = [
        ('ID_CARDS', 'ID Cards & Badges'),
        ('ELECTRONICS', 'Electronics & Gadgets'),
        ('BOOKS', 'Books & Stationery'),
        ('BAGS', 'Bags & Backpacks'),
        ('KEYS', 'Keys & Keychains'),
        ('BOTTLES', 'Water Bottles & Flasks'),
        ('CLOTHING', 'Clothing & Apparel'),
        ('ACCESSORIES', 'Accessories & Watches'),
        ('OTHER', 'Other Belongings'),
    ]

    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLAIM_PENDING', 'Claim Pending'),
        ('RECOVERED', 'Recovered'),
    ]

    CAMPUS_LOCATIONS = [
        ('Central Library', 'Central Library'),
        ('Main Academic Block', 'Main Academic Block'),
        ('Computer Science Lab', 'Computer Science Lab'),
        ('Science & Research Block', 'Science & Research Block'),
        ('Engineering Block', 'Engineering Block'),
        ('Student Canteen & Food Court', 'Student Canteen & Food Court'),
        ('Sports Complex & Ground', 'Sports Complex & Ground'),
        ('Main Auditorium', 'Main Auditorium'),
        ('Hostel Block - Boys', 'Hostel Block - Boys'),
        ('Hostel Block - Girls', 'Hostel Block - Girls'),
        ('Administrative Building', 'Administrative Building'),
        ('Parking Lot', 'Parking Lot'),
        ('Campus Bus Stop', 'Campus Bus Stop'),
        ('Other Campus Area', 'Other Campus Area'),
    ]

    title = models.CharField(max_length=200, help_text="Brief, descriptive title (e.g., 'Blue Dell Laptop Bag')")
    description = models.TextField(help_text="Detailed description of the item. Do not include sensitive codes or personal phone numbers.")
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    report_type = models.CharField(max_length=10, choices=REPORT_TYPE_CHOICES, default='LOST')
    campus_location = models.CharField(max_length=100, help_text="Where the item was lost or found on campus")
    date_lost_or_found = models.DateField(default=timezone.now, help_text="Date when item was lost or found")
    image = models.ImageField(upload_to='item_images/', blank=True, null=True, help_text="Optional photo of the item (Max 5MB, JPG/PNG/WEBP)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='items')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Privacy and Moderation
    is_flagged = models.BooleanField(default=False, help_text="Marked by community for moderation review")
    flag_reason = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['report_type', 'status']),
            models.Index(fields=['category']),
            models.Index(fields=['campus_location']),
            models.Index(fields=['date_lost_or_found']),
        ]

    def __str__(self):
        return f"[{self.get_report_type_display()}] {self.title} ({self.get_status_display()})"

    def get_absolute_url(self):
        return reverse('item_detail', kwargs={'pk': self.pk})

    @property
    def is_open(self):
        return self.status == 'OPEN'

    @property
    def is_claim_pending(self):
        return self.status == 'CLAIM_PENDING'

    @property
    def is_recovered(self):
        return self.status == 'RECOVERED'

    @property
    def report_type_badge(self):
        return 'danger' if self.report_type == 'LOST' else 'info'

    @property
    def status_badge(self):
        mapping = {
            'OPEN': 'primary',
            'CLAIM_PENDING': 'warning text-dark',
            'RECOVERED': 'success',
        }
        return mapping.get(self.status, 'secondary')


class RecoveryRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved (Pending Handover)'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed & Recovered'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='recovery_requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recovery_claims')
    message = models.TextField(help_text="Describe identifying marks, contents, or proof of ownership.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    owner_notes = models.TextField(blank=True, default='', help_text="Private instructions or response from listing owner")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            # Ensure a user does not submit multiple pending/approved claims on the same item
            models.UniqueConstraint(
                fields=['item', 'requester'],
                condition=models.Q(status__in=['PENDING', 'APPROVED']),
                name='unique_active_claim_per_user'
            )
        ]

    def __str__(self):
        return f"Claim by {self.requester.username} for '{self.item.title}' ({self.get_status_display()})"

    @property
    def status_badge(self):
        mapping = {
            'PENDING': 'warning text-dark',
            'APPROVED': 'info',
            'REJECTED': 'danger',
            'COMPLETED': 'success',
        }
        return mapping.get(self.status, 'secondary')


class ItemReport(models.Model):
    REASON_CHOICES = [
        ('SPAM', 'Spam or irrelevant listing'),
        ('SENSITIVE_INFO', 'Contains sensitive info (full ID number, phone, card digits)'),
        ('INAPPROPRIATE_CONTENT', 'Inappropriate or abusive image/description'),
        ('FAKE_LISTING', 'Fake or fraudulent claim/listing'),
        ('OTHER', 'Other issue'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='reports')
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reported_items')
    reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    details = models.TextField(blank=True, help_text="Additional information about why this listing was reported.")
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Report for '{self.item.title}' - {self.get_reason_display()}"


class FAQ(models.Model):
    CATEGORY_CHOICES = [
        ('REPORTING', 'Reporting Lost & Found'),
        ('SEARCH', 'Search & Filtering'),
        ('CLAIMS', 'Claims & Ownership Verification'),
        ('SAFETY', 'Safety, Privacy & Handovers'),
        ('TECHNICAL', 'Technical & Error Codes'),
        ('ACCOUNT', 'Accounts & Permissions'),
    ]

    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='REPORTING')
    order = models.PositiveIntegerField(default=0, help_text="Ordering position in FAQ list")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'id']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question


class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High - Urgent'),
    ]

    ticket_number = models.CharField(max_length=32, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='support_tickets')
    contact_email = models.EmailField(help_text="Student or staff email for reply notifications")
    subject = models.CharField(max_length=200)
    message = models.TextField(help_text="Detailed description of the inquiry or technical error")
    related_error_code = models.CharField(max_length=20, blank=True, help_text="e.g. 404, 403, 500, CLF-1001")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    ai_session_id = models.CharField(max_length=64, blank=True, help_text="Linked MongoDB AI chat session if created via assistant")
    admin_notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            import uuid
            self.ticket_number = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.ticket_number}] {self.subject} ({self.get_status_display()})"

    @property
    def status_badge(self):
        colors = {
            'OPEN': 'warning text-dark',
            'IN_PROGRESS': 'info',
            'RESOLVED': 'success',
            'CLOSED': 'secondary',
        }
        return colors.get(self.status, 'secondary')

