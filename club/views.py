import json
import logging
import uuid
from urllib.parse import quote
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

import razorpay
from .models import Event, GalleryImage, Member, SiteSettings
from .forms import RegistrationForm

logger = logging.getLogger(__name__)


def home_view(request):
    """Render the main landing page with dynamic content from the database."""
    events = Event.objects.filter(is_active=True)
    gallery_images = GalleryImage.objects.filter(is_visible=True)
    form = RegistrationForm()
    settings = SiteSettings.load()

    context = {
        'events': events,
        'gallery_images': gallery_images,
        'form': form,
        'settings': settings,
    }
    return render(request, 'club/home.html', context)


def register_view(request):
    """Handle registration form submission and redirect to payment."""
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            member = form.save(commit=False)
            member.payment_status = 'pending'
            member.save()
            return redirect('payment', member_id=member.pk)
        else:
            events = Event.objects.filter(is_active=True)
            gallery_images = GalleryImage.objects.filter(is_visible=True)
            settings = SiteSettings.load()
            context = {
                'events': events,
                'gallery_images': gallery_images,
                'form': form,
                'settings': settings,
                'scroll_to_register': True,
            }
            return render(request, 'club/home.html', context)
    return redirect('home')


def payment_view(request, member_id):
    """Display UPI / Razorpay payment page after registration."""
    member = get_object_or_404(Member, pk=member_id)
    settings = SiteSettings.load()

    razorpay_order_id = member.razorpay_order_id

    key_id = settings.razorpay_key_id.strip() if settings.razorpay_key_id else ''
    key_secret = settings.razorpay_key_secret.strip() if settings.razorpay_key_secret else ''

    is_razorpay_configured = bool(
        key_id
        and key_secret
        and key_id != 'rzp_test_52clubKeyId'
    )

    # Create/Refresh Razorpay Order matching current API keys
    if is_razorpay_configured:
        try:
            client = razorpay.Client(auth=(key_id, key_secret))
            amount_in_paise = int(settings.registration_fee * 100)
            order_data = {
                'amount': amount_in_paise,
                'currency': 'INR',
                'receipt': f'receipt_{member.pk}_{uuid.uuid4().hex[:6]}',
                'notes': {
                    'member_id': str(member.pk),
                    'transaction_id': str(member.transaction_id),
                    'email': member.email,
                    'full_name': member.full_name,
                }
            }
            order = client.order.create(data=order_data)
            razorpay_order_id = order.get('id')
            member.razorpay_order_id = razorpay_order_id
            member.save(update_fields=['razorpay_order_id'])
        except Exception as e:
            logger.warning(f"Razorpay Order creation notice: {e}")

    # UPI Deep Link — P2P compatible (no 'tr' param; GPay rejects it for personal VPAs)
    fee_str = f"{float(settings.registration_fee):.2f}"

    upi_url = (
        f"upi://pay?"
        f"pa={settings.upi_id.strip()}"
        f"&pn={quote(settings.upi_display_name.strip())}"
        f"&am={fee_str}"
        f"&cu=INR"
    )

    context = {
        'member': member,
        'settings': settings,
        'upi_url': upi_url,
        'transaction_id': str(member.transaction_id),
        'razorpay_order_id': razorpay_order_id or '',
        'razorpay_key_id': key_id,
        'is_razorpay_configured': is_razorpay_configured,
        'amount_in_paise': int(settings.registration_fee * 100),
    }
    return render(request, 'club/payment.html', context)


# ─────────────────────────────────────────────
# API: Payment Status Polling
# ─────────────────────────────────────────────

@require_GET
def check_payment_status(request, transaction_id):
    """
    JSON endpoint polled by frontend every 3 seconds.
    Returns current payment status for transaction.
    """
    try:
        member = Member.objects.get(transaction_id=transaction_id)
    except Member.DoesNotExist:
        return JsonResponse({'error': 'Transaction not found'}, status=404)

    return JsonResponse({
        'transaction_id': str(member.transaction_id),
        'status': member.payment_status,
        'member_name': member.full_name,
        'member_id': member.pk,
    })


# ─────────────────────────────────────────────
# API: Verify Razorpay Checkout Signature
# ─────────────────────────────────────────────

@csrf_exempt
@require_POST
def verify_razorpay_payment(request):
    """
    Called after successful Razorpay modal checkout on frontend.
    Verifies Razorpay HMAC signature and updates member status to completed.
    """
    try:
        data = json.loads(request.body)
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')
        transaction_id = data.get('transaction_id')

        member = get_object_or_404(Member, transaction_id=transaction_id)
        settings = SiteSettings.load()

        if settings.razorpay_key_id and settings.razorpay_key_secret and razorpay_signature and settings.razorpay_key_id != 'rzp_test_52clubKeyId':
            client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            client.utility.verify_payment_signature(params_dict)

        member.payment_status = 'completed'
        member.razorpay_payment_id = razorpay_payment_id
        member.save()

        return JsonResponse({
            'success': True,
            'member_id': member.pk,
            'status': 'completed'
        })
    except Exception as e:
        logger.error(f"Payment verification failed: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ─────────────────────────────────────────────
# API: Payment Webhook Receiver
# ─────────────────────────────────────────────

@csrf_exempt
@require_POST
def payment_webhook(request):
    """
    Unified Webhook Endpoint:
    Processes official Razorpay webhook events (payment.captured)
    as well as simulated test webhooks.
    """
    settings = SiteSettings.load()

    # Razorpay Webhook Verification
    razorpay_signature = request.headers.get('X-Razorpay-Signature')
    if razorpay_signature and settings.razorpay_key_secret and settings.razorpay_key_id != 'rzp_test_52clubKeyId':
        try:
            client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
            client.utility.verify_webhook_signature(
                request.body.decode('utf-8'),
                razorpay_signature,
                settings.webhook_secret
            )
            data = json.loads(request.body)
            event_type = data.get('event')
            if event_type in ['payment.captured', 'order.paid']:
                payload = data.get('payload', {}).get('payment', {}).get('entity', {})
                notes = payload.get('notes', {})
                tx_id = notes.get('transaction_id')
                payment_id = payload.get('id')

                if tx_id:
                    member = Member.objects.get(transaction_id=tx_id)
                    member.payment_status = 'completed'
                    member.razorpay_payment_id = payment_id
                    member.save()
                    return JsonResponse({'status': 'ok'})
        except Exception as e:
            logger.error(f"Razorpay webhook verification error: {e}")
            return JsonResponse({'error': str(e)}, status=400)

    # Standard JSON body webhook (for testing/custom gateway)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    transaction_id = data.get('transaction_id')
    status = data.get('status')
    secret = data.get('secret')

    if not all([transaction_id, status, secret]):
        return JsonResponse({'error': 'Missing required fields: transaction_id, status, secret'}, status=400)

    if secret != settings.webhook_secret:
        return JsonResponse({'error': 'Invalid webhook secret'}, status=403)

    if status not in ['completed', 'failed']:
        return JsonResponse({'error': 'Status must be "completed" or "failed"'}, status=400)

    try:
        member = Member.objects.get(transaction_id=transaction_id)
        member.payment_status = status
        member.save()
        return JsonResponse({
            'success': True,
            'transaction_id': str(member.transaction_id),
            'status': member.payment_status,
            'member_name': member.full_name,
        })
    except Member.DoesNotExist:
        return JsonResponse({'error': 'Transaction not found'}, status=404)


def payment_success_view(request, member_id):
    """Show success page after payment is confirmed."""
    member = get_object_or_404(Member, pk=member_id)
    return render(request, 'club/payment_success.html', {'member': member})
