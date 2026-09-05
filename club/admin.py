from django.contrib import admin
from django.utils.html import format_html
from .models import Event, GalleryImage, Member, SiteSettings


# ─────────────────────────────────────────────
# Admin Site Customization
# ─────────────────────────────────────────────

admin.site.site_header = 'THE 52 CLUB — Admin Panel'
admin.site.site_title = 'The 52 Club Admin'
admin.site.index_title = 'Manage Your Club'


# ─────────────────────────────────────────────
# Event Admin
# ─────────────────────────────────────────────

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('event_number', 'title', 'venue', 'date_text', 'time_text', 'collaborations', 'is_active', 'order')
    list_display_links = ('event_number', 'title')
    list_editable = ('venue', 'is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('event_number', 'title', 'venue', 'description', 'collaborations')
    fieldsets = (
        ('Event Overview', {
            'fields': ('event_number', 'tags', 'title', 'description', 'image'),
            'description': '⚡ Main identity and visual banner for the event.'
        }),
        ('Venue & Schedule', {
            'fields': ('venue', 'date_text', 'time_text'),
            'description': '📍 Update the event venue, date, and time here.'
        }),
        ('Collaborations & Photos Drive Link', {
            'fields': ('collaborations', 'google_drive_link'),
            'description': '🤝 Add collaborators/partners and Google Drive link for event photo gallery.'
        }),
        ('Display Settings', {
            'fields': ('is_active', 'order')
        }),
    )


# ─────────────────────────────────────────────
# Gallery Admin
# ─────────────────────────────────────────────

@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('image_preview', 'caption', 'order', 'is_visible', 'uploaded_at')
    list_editable = ('caption', 'order', 'is_visible')
    list_filter = ('is_visible',)
    search_fields = ('caption',)
    readonly_fields = ('image_preview_large', 'uploaded_at')

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 80px; height: 60px; '
                'object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return '—'
    image_preview.short_description = 'Preview'

    def image_preview_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 400px; max-height: 300px; '
                'border-radius: 8px;" />',
                obj.image.url
            )
        return '—'
    image_preview_large.short_description = 'Image Preview'

    fieldsets = (
        ('Image', {
            'fields': ('image', 'image_preview_large')
        }),
        ('Details', {
            'fields': ('caption', 'order', 'is_visible')
        }),
    )


# ─────────────────────────────────────────────
# Member Admin
# ─────────────────────────────────────────────

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 'email', 'phone', 'experience',
        'payment_status_badge', 'transaction_id', 'registered_at'
    )
    list_filter = ('payment_status', 'experience', 'registered_at')
    search_fields = ('full_name', 'email', 'phone', 'transaction_id')
    list_editable = ()
    readonly_fields = ('transaction_id', 'registered_at')
    actions = ['mark_payment_completed', 'mark_payment_failed']

    def payment_status_badge(self, obj):
        colors = {
            'pending': '#f0ad4e',
            'completed': '#5cb85c',
            'failed': '#d9534f',
        }
        color = colors.get(obj.payment_status, '#999')
        return format_html(
            '<span style="background: {}; color: #fff; padding: 3px 10px; '
            'border-radius: 12px; font-size: 11px; font-weight: bold; '
            'text-transform: uppercase;">{}</span>',
            color, obj.payment_status
        )
    payment_status_badge.short_description = 'Payment'
    payment_status_badge.admin_order_field = 'payment_status'

    fieldsets = (
        ('Personal Information', {
            'fields': ('full_name', 'email', 'phone')
        }),
        ('Registration Details', {
            'fields': ('experience', 'message')
        }),
        ('Payment', {
            'fields': ('transaction_id', 'payment_status')
        }),
        ('Timestamps', {
            'fields': ('registered_at',),
            'classes': ('collapse',)
        }),
    )

    @admin.action(description='✅ Mark selected members as payment completed')
    def mark_payment_completed(self, request, queryset):
        updated = queryset.update(payment_status='completed')
        self.message_user(request, f'{updated} member(s) marked as payment completed.')

    @admin.action(description='❌ Mark selected members as payment failed')
    def mark_payment_failed(self, request, queryset):
        updated = queryset.update(payment_status='failed')
        self.message_user(request, f'{updated} member(s) marked as payment failed.')


# ─────────────────────────────────────────────
# Site Settings Admin (Singleton)
# ─────────────────────────────────────────────

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'registration_fee_display', 'upi_id', 'razorpay_key_id', 'webhook_secret')
    fieldsets = (
        ('UPI Payment Settings', {
            'fields': ('registration_fee', 'upi_id', 'upi_display_name')
        }),
        ('Razorpay API Keys Settings', {
            'fields': ('razorpay_key_id', 'razorpay_key_secret'),
            'description': '⚡ Enter your Razorpay Key ID (rzp_test_...) and Key Secret from Razorpay Dashboard (Settings → API Keys).'
        }),
        ('Webhook Security', {
            'fields': ('webhook_secret',),
            'description': 'Secret key used by your payment gateway or external script to POST payment confirmation webhooks.'
        }),
    )

    def registration_fee_display(self, obj):
        return format_html('₹ {}', obj.registration_fee)
    registration_fee_display.short_description = 'Registration Fee'

    def has_add_permission(self, request):
        """Prevent creating more than one SiteSettings instance."""
        if SiteSettings.objects.exists():
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting SiteSettings."""
        return False

