import uuid
from django.db import models
from django.utils import timezone


class Event(models.Model):
    """Represents a club event/session with editable location, venue, drive link, and metadata."""
    event_number = models.CharField(
        max_length=20,
        default='01',
        help_text='Event number display (e.g., "01", "02", "SESSION #1")'
    )
    tags = models.CharField(
        max_length=200,
        blank=True,
        default='RUNNING, CHALLENGE, COMMUNITY',
        help_text='Comma-separated tags (e.g., "RUNNING, CHALLENGE, COMMUNITY")'
    )
    title = models.CharField(max_length=200, default='SEVEN CHALLENGES — ONE FINISH')
    description = models.TextField(
        blank=True,
        default='Seven challenges. One finish. The beginning of the 52 Club.'
    )
    image = models.ImageField(
        upload_to='events/',
        blank=True,
        null=True,
        help_text='Upload event banner/photo'
    )
    venue = models.CharField(
        max_length=300,
        default='EDEN GARDENS TURF, ANANTAPUR',
        help_text='Event venue location'
    )
    date_text = models.CharField(
        max_length=100,
        default='SUNDAY, 23RD AUGUST',
        help_text='Display text for the date'
    )
    time_text = models.CharField(
        max_length=50,
        default='6:30 AM',
        help_text='Display text for the time'
    )
    collaborations = models.CharField(
        max_length=200,
        blank=True,
        default='7 FINISHERS',
        help_text='Collaborations, partners, or event highlights'
    )
    google_drive_link = models.URLField(
        blank=True,
        help_text='Google Drive URL for event photos/videos'
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
        return f"#{self.event_number} {self.title} — {self.venue}"

    @property
    def location(self):
        """Backward compatibility helper for location."""
        return self.venue


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
