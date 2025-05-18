import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
import sqlite3

# --- Configuration ---
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USERNAME = 'mukundjaivalmadproject@gmail.com'
SMTP_PASSWORD = 'wmra zwfx ydrn gcoi'
SENDER_EMAIL = 'mukundjaivalmadproject@gmail.com'
SENDER_NAME = "Community Pulse Team"
DB_PATH = './instance/community_pulse.db'


def test_smtp_connection():
    print("\n--- Testing SMTP connection ---")
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.quit()
        print("SMTP login test successful.\n")
    except Exception as e:
        print(f"SMTP login test failed: {e}\n")


def get_event_details_and_attendees(event_id):
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
        if '.' in start_dt_str:
            start_dt_str = start_dt_str.split('.')[0]
        start_datetime_obj = datetime.fromisoformat(start_dt_str.replace('Z', '+00:00'))
        if start_datetime_obj.tzinfo is None:
            start_datetime_obj = start_datetime_obj.replace(tzinfo=timezone.utc)

        event_details = {
            "id": event_id,
            "title": title,
            "start_datetime": start_datetime_obj,
            "location_address": location,
            "status": status
        }

        cursor.execute("""
            SELECT guest_name, guest_email, guest_phone, num_people
            FROM rsvps
            WHERE event_id = ?
        """, (event_id,))
        attendees = [
            {"name": row[0] or "Valued Attendee", "email": row[1], "phone": row[2], "num_people": row[3]}
            for row in cursor.fetchall() if row[1]
        ]

        print(f"Found event '{title}' with {len(attendees)} attendees with emails.")
        return event_details, attendees

    except Exception as e:
        print(f"Error fetching event/attendees: {e}")
        return None, []
    finally:
        if conn:
            conn.close()


def send_email_notification(name, email, subject, html_body, text_body):
    print(f"Attempting to send email to {email}...")
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg['To'] = email

        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SENDER_EMAIL, email, msg.as_string())
        server.quit()
        print(f"Email sent to {email}")
        return True
    except Exception as e:
        print(f"Failed to send email to {email}: {e}")
        return False


def send_reminder_email(name, email, title, start_datetime, location):
    subject = f"Reminder: Event '{title}' is tomorrow!"
    event_date_str = start_datetime.astimezone().strftime('%A, %B %d, %Y')
    event_time_str = start_datetime.astimezone().strftime('%I:%M %p %Z')

    html = f"""
    <html><body>
        <p>Hi {name},</p>
        <p>This is a friendly reminder that <strong>{title}</strong> is tomorrow, <strong>{event_date_str}</strong> at <strong>{event_time_str}</strong>.</p>
        <p><strong>Location:</strong> {location}</p>
        <p>See you there!</p>
        <p>– {SENDER_NAME}</p>
    </body></html>
    """

    text = f"""
    Hi {name},

    This is a friendly reminder that '{title}' is tomorrow, {event_date_str} at {event_time_str}.

    Location: {location}

    See you there!
    – {SENDER_NAME}
    """
    return send_email_notification(name, email, subject, html, text)


def get_upcoming_events_and_attendees_from_db():
    print("\n--- Fetching upcoming events for tomorrow ---")
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        tomorrow_date_str = (datetime.now(timezone.utc) + timedelta(days=1)).strftime('%Y-%m-%d')
        print(f"Tomorrow (UTC): {tomorrow_date_str}")

        cursor.execute("""
            SELECT id, title, start_datetime, location_address
            FROM events
            WHERE STRFTIME('%Y-%m-%d', start_datetime) = ? AND status = 'APPROVED'
        """, (tomorrow_date_str,))
        events = cursor.fetchall()
        print(f"Found {len(events)} event(s) for tomorrow.")

        upcoming = []
        for eid, title, start_dt_str, location in events:
            if '.' in start_dt_str:
                start_dt_str = start_dt_str.split('.')[0]
            start_dt = datetime.fromisoformat(start_dt_str.replace('Z', '+00:00'))
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=timezone.utc)

            cursor.execute("""
                SELECT guest_name, guest_email, guest_phone, num_people
                FROM rsvps WHERE event_id = ?
            """, (eid,))
            attendees = [
                {"name": row[0] or "Valued Attendee", "email": row[1], "phone": row[2], "num_people": row[3]}
                for row in cursor.fetchall() if row[1]
            ]
            if attendees:
                upcoming.append({
                    "id": eid,
                    "title": title,
                    "start_datetime": start_dt,
                    "location_address": location,
                    "attendees": attendees
                })
                print(f"Event '{title}' has {len(attendees)} attendee(s) with email.")
            else:
                print(f"Event '{title}' has no attendees with email.")
        return upcoming

    except Exception as e:
        print(f"Database error: {e}")
        return []
    finally:
        if conn:
            conn.close()


def send_daily_reminders():
    print(f"\n--- Starting daily reminders at {datetime.now().astimezone()} ---")
    events = get_upcoming_events_and_attendees_from_db()
    if not events:
        print("No events for tomorrow or no attendees.")
        return

    total_sent = 0
    total_failed = 0
    sent_set = set()

    for event in events:
        for attendee in event['attendees']:
            key = (attendee['email'], event['id'])
            if key in sent_set:
                continue
            if send_reminder_email(
                attendee["name"],
                attendee["email"],
                event["title"],
                event["start_datetime"],
                event["location_address"]
            ):
                total_sent += 1
            else:
                total_failed += 1
            sent_set.add(key)

    print(f"\n--- Reminder Summary ---")
    print(f"Emails sent: {total_sent}")
    print(f"Emails failed: {total_failed}")


# --- Entry point ---
if __name__ == "__main__":
    if not SMTP_USERNAME or not SMTP_PASSWORD or not SENDER_EMAIL:
        print("SMTP configuration missing. Please update the values at the top of the script.")
    elif 'path/to/your' in DB_PATH:
        print("DB_PATH is not set correctly.")
    else:
        test_smtp_connection()
        send_daily_reminders()