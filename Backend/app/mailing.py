import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
# No need for os or dotenv if not using .env file

# --- Configuration (EDIT THESE VALUES DIRECTLY) ---
# (Same SMTP and DB_PATH configuration as before)
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USERNAME = 'mukundjaivalmadproject@gmail.com'
SMTP_PASSWORD = 'wmra zwfx ydrn gcoi'
SENDER_EMAIL = 'mukundjaivalmadproject@gmail.com'
SENDER_NAME = "Community Pulse Team"
DB_PATH = './instance/community_pulse.db' # IMPORTANT: Update this path


# --- Helper Functions (get_upcoming_events_and_attendees_from_db remains the same) ---
# (send_reminder_email remains mostly the same, but we can generalize it slightly)

def get_event_details_and_attendees(event_id):
    """
    Fetches details for a specific event and its attendees from the database.
    """
    print(f"Fetching details for event ID {event_id} and its attendees...")
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, title, start_datetime, location_address, status
            FROM events
            WHERE id = ?
        """, (event_id,))
        event_row = cursor.fetchone()

        if not event_row:
            print(f"No event found with ID {event_id}.")
            return None, []

        event_id, title, start_dt_str, location, status = event_row
        try:
            if '.' in start_dt_str:
                start_dt_str = start_dt_str.split('.')[0]
            try:
                start_datetime_obj = datetime.fromisoformat(start_dt_str.replace('Z', '+00:00'))
            except ValueError:
                start_datetime_obj = datetime.fromisoformat(start_dt_str)
            if start_datetime_obj.tzinfo is None:
                start_datetime_obj = start_datetime_obj.replace(tzinfo=timezone.utc)
        except ValueError as e_parse:
            print(f"Could not parse datetime string '{start_dt_str}' for event ID {event_id}: {e_parse}.")
            return None, [] # Or handle more gracefully

        event_details = {
            "id": event_id,
            "title": title,
            "start_datetime": start_datetime_obj,
            "location_address": location,
            "status": status
        }

        current_event_attendees = []
        cursor.execute("""
            SELECT guest_name, guest_email, guest_phone, num_people
            FROM rsvps
            WHERE event_id = ?
        """, (event_id,))
        rsvp_rows = cursor.fetchall()

        for rsvp_row in rsvp_rows:
            guest_name, guest_email, guest_phone, num_people = rsvp_row
            if guest_email:
                current_event_attendees.append({
                    "name": guest_name or "Valued Attendee",
                    "email": guest_email,
                    "phone": guest_phone,
                    "num_people": num_people
                })
        
        print(f"Found event '{title}' with {len(current_event_attendees)} attendees with emails.")
        return event_details, current_event_attendees

    except sqlite3.Error as e:
        print(f"Database error in get_event_details_and_attendees: {e}")
        return None, []
    except Exception as e_global:
        print(f"An unexpected error occurred in get_event_details_and_attendees: {e_global}")
        return None, []
    finally:
        if conn:
            conn.close()


def send_email_notification(recipient_name, recipient_email, subject, html_body, text_body):
    """Generic function to send an email."""
    if not all([SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SENDER_EMAIL]):
        print("SMTP configuration is incomplete. Cannot send email.")
        return False

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg['To'] = recipient_email

    part1 = MIMEText(text_body, 'plain', 'utf-8')
    part2 = MIMEText(html_body, 'html', 'utf-8')
    msg.attach(part1)
    msg.attach(part2)

    try:
        if SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        else:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.ehlo()
            server.starttls()
            server.ehlo()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        server.quit()
        print(f"Successfully sent email '{subject}' to {recipient_email}.")
        return True
    except smtplib.SMTPAuthenticationError:
        print(f"SMTP Authentication Error for {SMTP_USERNAME}. Check credentials/settings.")
        return False
    except Exception as e:
        print(f"Failed to send email to {recipient_email} for subject '{subject}': {e}")
        return False

# --- Reminder Email Function (Uses generic send_email_notification) ---
def send_reminder_email(attendee_name, attendee_email, event_title, event_start_datetime, event_location):
    subject = f"Reminder: Event '{event_title}' is tomorrow!"
    local_start_time_str = event_start_datetime.astimezone().strftime('%I:%M %p %Z')
    event_date_str = event_start_datetime.astimezone().strftime('%A, %B %d, %Y')

    body_html = f"""
    <html><head><style>body {{font-family: Arial, sans-serif; margin: 20px;}} p {{margin-bottom: 10px;}} strong {{color: #333;}}</style></head>
    <body>
        <p>Hi {attendee_name},</p>
        <p>This is a friendly reminder that the event "<strong>{event_title}</strong>" is scheduled for tomorrow, <strong>{event_date_str}</strong>, starting around <strong>{local_start_time_str}</strong>.</p>
        <p><strong>Location:</strong> {event_location}</p>
        <p>We're looking forward to seeing you there!</p>
        <p>Best regards,<br/>The {SENDER_NAME}</p>
    </body>
    </html>
    """
    body_text = f"Hi {attendee_name},\n\nThis is a friendly reminder that the event \"{event_title}\" is scheduled for tomorrow, {event_date_str}, starting around {local_start_time_str}.\n\nLocation: {event_location}\n\nWe're looking forward to seeing you there!\n\nBest regards,\nThe {SENDER_NAME}"
    return send_email_notification(attendee_name, attendee_email, subject, body_html, body_text)


# --- NEW: Event Change Notification Function ---
def send_event_change_notification_to_attendees(event_id, change_summary, custom_message=""):
    """
    Sends a notification to all attendees of a specific event about a change.
    - event_id: The ID of the event that changed.
    - change_summary: A short summary of what changed (e.g., "Location Updated", "Event Cancelled", "Time Changed").
    - custom_message: An optional additional message from the organizer.
    """
    print(f"\n--- Sending change notifications for event ID {event_id} ---")
    print(f"Change Summary: {change_summary}")
    if custom_message:
        print(f"Custom Message: {custom_message}")

    event_details, attendees = get_event_details_and_attendees(event_id)

    if not event_details:
        print(f"Cannot send change notifications: Event ID {event_id} not found.")
        return 0, 0 # emails_sent, emails_failed

    if not attendees:
        print(f"No attendees with emails found for event ID {event_id} to notify.")
        return 0, 0

    emails_sent = 0
    emails_failed = 0

    subject = f"Update for Event: {event_details['title']} - {change_summary}"

    for attendee in attendees:
        attendee_name = attendee.get("name", "Valued Attendee")
        attendee_email = attendee.get("email")

        if not attendee_email:
            continue

        # Construct email body for the change
        # Format current event details for the email
        event_title = event_details['title']
        start_datetime_obj = event_details['start_datetime']
        current_location = event_details['location_address']
        current_status = event_details['status']

        local_start_time_str = start_datetime_obj.astimezone().strftime('%I:%M %p %Z')
        event_date_str = start_datetime_obj.astimezone().strftime('%A, %B %d, %Y')

        html_body = f"""
        <html><head><style>body {{font-family: Arial, sans-serif; margin: 20px;}} p {{margin-bottom: 10px;}} strong {{color: #333;}} .highlight {{color: #d9534f; font-weight: bold;}}</style></head>
        <body>
            <p>Hi {attendee_name},</p>
            <p>There's an important update regarding the event "<strong>{event_title}</strong>" you RSVP'd for.</p>
            <p class="highlight">Change: {change_summary}</p>
            {f'<p><strong>Organizer message:</strong> {custom_message}</p>' if custom_message else ''}
            <p>Please review the current event details:</p>
            <ul>
                <li><strong>Event:</strong> {event_title}</li>
                <li><strong>Date:</strong> {event_date_str}</li>
                <li><strong>Time:</strong> {local_start_time_str}</li>
                <li><strong>Location:</strong> {current_location}</li>
                <li><strong>Status:</strong> {current_status}</li>
            </ul>
            <p>If you have any questions, please contact the event organizer.</p>
            <p>Best regards,<br/>The {SENDER_NAME}</p>
        </body>
        </html>
        """
        text_body = f"""
        Hi {attendee_name},

        There's an important update regarding the event "{event_title}" you RSVP'd for.
        Change: {change_summary}
        {f'Organizer message: {custom_message}' if custom_message else ''}

        Please review the current event details:
        - Event: {event_title}
        - Date: {event_date_str}
        - Time: {local_start_time_str}
        - Location: {current_location}
        - Status: {current_status}

        If you have any questions, please contact the event organizer.

        Best regards,
        The {SENDER_NAME}
        """

        if send_email_notification(attendee_name, attendee_email, subject, html_body, text_body):
            emails_sent += 1
        else:
            emails_failed += 1
            
    print(f"Change notification process for event ID {event_id} finished.")
    print(f"Emails sent: {emails_sent}, Emails failed: {emails_failed}")
    return emails_sent, emails_failed


# --- Main Daily Reminder Logic (get_upcoming_events_and_attendees_from_db, send_daily_reminders as before) ---
def get_upcoming_events_and_attendees_from_db():
    # ... (same as your previously corrected version) ...
    print("Fetching upcoming events and attendees from database...")
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        tomorrow_date_str = (datetime.now(timezone.utc) + timedelta(days=1)).strftime('%Y-%m-%d')
        cursor.execute("""
            SELECT id, title, start_datetime, location_address
            FROM events
            WHERE STRFTIME('%Y-%m-%d', start_datetime) = ? AND status = 'APPROVED'
        """, (tomorrow_date_str,))
        event_rows = cursor.fetchall()
        events_for_tomorrow_with_attendees = []
        if not event_rows:
            print(f"No approved events found for tomorrow ({tomorrow_date_str}).")
            return events_for_tomorrow_with_attendees
        for event_row in event_rows:
            event_id, title, start_dt_str, location = event_row
            try:
                if '.' in start_dt_str: start_dt_str = start_dt_str.split('.')[0]
                try: start_datetime_obj = datetime.fromisoformat(start_dt_str.replace('Z', '+00:00'))
                except ValueError: start_datetime_obj = datetime.fromisoformat(start_dt_str)
                if start_datetime_obj.tzinfo is None: start_datetime_obj = start_datetime_obj.replace(tzinfo=timezone.utc)
            except ValueError as e_parse:
                print(f"Could not parse datetime string '{start_dt_str}' for event ID {event_id} (reminder): {e_parse}. Skipping.")
                continue
            current_event_attendees = []
            cursor.execute("""
                SELECT guest_name, guest_email, guest_phone, num_people
                FROM rsvps WHERE event_id = ?
            """, (event_id,))
            for rsvp_row in cursor.fetchall():
                if rsvp_row[1]: current_event_attendees.append({"name": rsvp_row[0] or "Valued Attendee", "email": rsvp_row[1], "phone": rsvp_row[2], "num_people": rsvp_row[3]})
            if current_event_attendees:
                events_for_tomorrow_with_attendees.append({"id": event_id, "title": title, "start_datetime": start_datetime_obj, "location_address": location, "attendees": current_event_attendees})
            else: print(f"Event ID {event_id} ('{title}') has no attendees with emails for reminders.")
        print(f"Found {len(events_for_tomorrow_with_attendees)} events for tomorrow with attendees for reminders.")
        return events_for_tomorrow_with_attendees
    except sqlite3.Error as e: print(f"Database error in get_upcoming_events_and_attendees_from_db: {e}"); return []
    except Exception as e_global: print(f"An unexpected error in get_upcoming_events_and_attendees_from_db: {e_global}"); return []
    finally:
        if conn: conn.close()

def send_daily_reminders():
    print(f"\n--- Starting daily reminder process at {datetime.now(timezone.utc).astimezone()} ---")
    events_to_remind = get_upcoming_events_and_attendees_from_db()
    if not events_to_remind:
        print("No events for tomorrow requiring reminders or no attendees found.")
        return
    total_emails_sent, total_emails_failed = 0, 0
    sent_to_for_event = set()
    for event in events_to_remind:
        for attendee in event.get("attendees", []):
            if not attendee.get("email") or (attendee.get("email"), event["id"]) in sent_to_for_event: continue
            if send_reminder_email(attendee["name"], attendee["email"], event["title"], event["start_datetime"], event["location_address"]):
                total_emails_sent += 1
            else: total_emails_failed += 1
            sent_to_for_event.add((attendee["email"], event["id"]))
    print(f"\n--- Daily reminder process finished ---")
    print(f"Total reminder emails successfully sent: {total_emails_sent}")
    print(f"Total reminder emails failed: {total_emails_failed}")


# --- Execution & SQLite Import ---
if __name__ == "__main__":
    try:
        import sqlite3
    except ImportError:
        print("The 'sqlite3' module is required. Please ensure your Python installation includes it.")
        exit(1)

    if 'path/to/your' in DB_PATH:
        print("ERROR: DB_PATH variable needs to be updated at the top of the script.")
        exit(1)
    if not SMTP_USERNAME or 'your_email@example.com' in SMTP_USERNAME:
        print("ERROR: SMTP configuration variables need to be updated at the top of the script.")
        exit(1)

    # Example usage:
    # To send daily reminders (as before):
    # send_daily_reminders()

    # To send a change notification for a specific event:
    # Make sure an event with ID 1 exists and has attendees in your DB for this to work
    print("\n\n--- Example: Sending Event Change Notification ---")
    # You would get this event_id from your Flask app when a change is made
    target_event_id = 1 
    # You would determine this summary based on what changed in Flask
    change_description_summary = "Location Updated" 
    # Optional message from organizer
    organizer_note = "Please note the new venue is now the larger hall due to high demand." 
    
    # Check if the event exists before trying to send notifications
    # This check can be done more robustly
    _event_check, _attendees_check = get_event_details_and_attendees(target_event_id)
    if _event_check:
        sent_count, failed_count = send_event_change_notification_to_attendees(
            target_event_id,
            change_description_summary,
            custom_message=organizer_note
        )
        print(f"Event Change Notifications - Sent: {sent_count}, Failed: {failed_count}")
    else:
        print(f"Example change notification: Event ID {target_event_id} not found, no notifications sent.")

    # If you want to run daily reminders *after* the example change notification:
    # print("\n\n--- Running Daily Reminders After Example ---")
    # send_daily_reminders()