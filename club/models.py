import uuid
from django.db import models
from django.utils import timezone


class Event(models.Model):
    """Represents a club event/session with editable location."""
    title = models.CharField(max_length=200, default='THE 52 CLUB SESSION')
    description = models.TextField(
        blank=True,
        default='Join us for our weekly strength-based community session. '
                'Train together, push your limits and get stronger as a community.'
    )
    date_text = models.CharField(
        max_length=100,
        default='EVERY SUNDAY',
        help_text='Display text for the date (e.g., "EVERY SUNDAY", "SEP 15, 2026")'
    )
    time_text = models.CharField(
        max_length=50,
        default='7:00 AM',
        help_text='Display text for the time'
    )
    location = models.CharField(
        max_length=300,
        default='LOCATION ANNOUNCED WEEKLY',
        help_text='Update this to set the current event location'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Only active events are shown on the website'
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text='Lower numbers appear first'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'

    def __str__(self):
        return f"{self.title} — {self.location}"


class GalleryImage(models.Model):
    """Images uploaded to the gallery section."""
    image = models.ImageField(
        upload_to='gallery/',
        help_text='Upload high-quality images (recommended: 1200x800px or larger)'
    )
    caption = models.CharField(
        max_length=200,
        blank=True,
        help_text='Optional caption for the image'
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text='Lower numbers appear first'
    )
    is_visible = models.BooleanField(
        default=True,
        help_text='Only visible images are shown on the website'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-uploaded_at']
        verbose_name = 'Gallery Image'
        verbose_name_plural = 'Gallery Images'

    def __str__(self):
        return self.caption or f"Image #{self.pk}"


class Member(models.Model):
    """Registered members of the club."""
    EXPERIENCE_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    transaction_id = models.UUIDField(
        default=uuid.uuid4,
        db_index=True,
        editable=False,
        help_text='Unique transaction identifier for payment tracking'
    )
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    experience = models.CharField(
        max_length=20,
        choices=EXPERIENCE_CHOICES,
        default='beginner'
    )
    message = models.TextField(
        blank=True,
        help_text='What brings them to The 52 Club'
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    razorpay_order_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Razorpay Order ID created for this registration'
    )
    razorpay_payment_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Razorpay Payment ID captured after successful payment'
    )
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-registered_at']
        verbose_name = 'Member'
        verbose_name_plural = 'Members'

    def __str__(self):
        return f"{self.full_name} ({self.email})"


class SiteSettings(models.Model):
    """Singleton model for site-wide settings like fee and UPI."""
    registration_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=500.00,
        help_text='Registration fee in ₹ (INR)'
    )
    upi_id = models.CharField(
        max_length=100,
        default='8374446838@ybl',
        help_text='UPI ID for receiving payments'
    )
    upi_display_name = models.CharField(
        max_length=100,
        default='The 52 Club',
        help_text='Name displayed on UPI payment screen'
    )
    razorpay_key_id = models.CharField(
        max_length=100,
        default='rzp_test_52clubKeyId',
        blank=True,
        help_text='Your Razorpay Key ID (from Razorpay Dashboard)'
    )
    razorpay_key_secret = models.CharField(
        max_length=100,
        default='rzp_test_52clubKeySecret',
        blank=True,
        help_text='Your Razorpay Key Secret'
    )
    webhook_secret = models.CharField(
        max_length=100,
        default='the52club-webhook-secret',
        help_text='Secret key for authenticating webhook requests'
    )

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return 'Site Settings'

    def save(self, *args, **kwargs):
        """Ensure only one instance of SiteSettings exists."""
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Load the singleton instance, creating it if it doesn't exist."""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
