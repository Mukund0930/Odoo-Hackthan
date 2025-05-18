from flask_mail import Message
from .. import mail # mail object from app/__init__.py
from flask import current_app
# from twilio.rest import Client # If using Twilio

def send_email(to, subject, template_body):
    if not mail.state: # Check if mail is configured
        current_app.logger.error("Mail not configured. Cannot send email.")
        return
    msg = Message(
        subject,
        recipients=[to],
        html=template_body,
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    try:
        mail.send(msg)
        current_app.logger.info(f"Email sent to {to} with subject: {subject}")
    except Exception as e:
        current_app.logger.error(f"Failed to send email to {to}: {e}")


def send_event_reminder(event, user):
    if 'email' in user.notification_preference and user.email:
        subject = f"Reminder: Event '{event.title}' is tomorrow!"
        # You would ideally use Flask's render_template for HTML emails
        body = f"""
        <p>Hi {user.username},</p>
        <p>This is a reminder that the event '<strong>{event.title}</strong>' is scheduled for tomorrow, {event.start_datetime.strftime('%Y-%m-%d %I:%M %p')}.</p>
        <p>Location: {event.location_address}</p>
        <p>We look forward to seeing you there!</p>
        <p>Thanks,<br>The Community Pulse Team</p>
        """
        send_email(user.email, subject, body)
    # Add SMS/WhatsApp logic here if implemented

def send_event_update_notification(event, message_info, rsvp_user_or_guest_email):
    """
    Sends an update notification for an event.
    :param event: The Event object.
    :param message_info: A string describing the update (e.g., "Location Changed", "Cancelled").
    :param rsvp_user_or_guest_email: User object or guest email string.
    """
    if hasattr(rsvp_user_or_guest_email, 'email') and rsvp_user_or_guest_email.email and 'email' in rsvp_user_or_guest_email.notification_preference : # It's a User object
        to_email = rsvp_user_or_guest_email.email
        username = rsvp_user_or_guest_email.username
    elif isinstance(rsvp_user_or_guest_email, str): # It's a guest email string
        to_email = rsvp_user_or_guest_email
        username = "Guest"
    else:
        current_app.logger.warning(f"Cannot send update for event {event.id}, invalid recipient data.")
        return

    subject = f"Update for Event: {event.title} - {message_info}"
    body = f"""
    <p>Hi {username},</p>
    <p>There's an update regarding the event '<strong>{event.title}</strong>':</p>
    <p><strong>{message_info}</strong></p>
    <p>New Details (if applicable):</p>
    <p>Title: {event.title}</p>
    <p>Start Time: {event.start_datetime.strftime('%Y-%m-%d %I:%M %p')}</p>
    <p>Location: {event.location_address}</p>
    <p>Status: {event.status}</p>
    <p>Please check the event page for the latest information.</p>
    <p>Thanks,<br>The Community Pulse Team</p>
    """
    send_email(to_email, subject, body)
    # Add SMS/WhatsApp logic here

# Example SMS sending function (requires Twilio setup)
# def send_sms(to_phone_number, body):
#     if not current_app.config.get('TWILIO_ACCOUNT_SID'):
#         current_app.logger.error("Twilio not configured. Cannot send SMS.")
#         return
#     client = Client(current_app.config['TWILIO_ACCOUNT_SID'], current_app.config['TWILIO_AUTH_TOKEN'])
#     try:
#         message = client.messages.create(
#             body=body,
#             from_=current_app.config['TWILIO_PHONE_NUMBER'],
#             to=to_phone_number
#         )
#         current_app.logger.info(f"SMS sent to {to_phone_number}: {message.sid}")
#     except Exception as e:
#         current_app.logger.error(f"Failed to send SMS to {to_phone_number}: {e}")