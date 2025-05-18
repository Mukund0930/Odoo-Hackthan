from flask_restx import fields
from ..apis import api # Import the api object from apis/__init__.py

# Basic schema for event output
event_output_schema = api.model('EventOutput', {
    'id': fields.Integer(readonly=True, description='The event unique identifier'),
    'title': fields.String(required=True, description='Event title'),
    'description': fields.String(description='Event description'),
    'category': fields.String(required=True, description='Event category'),
    'start_datetime': fields.DateTime(dt_format='iso8601', required=True, description='Event start date and time'),
    'end_datetime': fields.DateTime(dt_format='iso8601', description='Event end date and time'),
    'location_address': fields.String(required=True, description='Event location'),
    'status': fields.String(description='Event status (PENDING, APPROVED, REJECTED, CANCELLED)'),
    'organizer_id': fields.Integer(description='ID of the event organizer'),
    'organizer_username': fields.String(attribute='organizer.username', description='Username of the event organizer'),
    'created_at': fields.DateTime(dt_format='iso8601', readonly=True),
    'attendees_count': fields.Integer(readonly=True, description='Number of people attending (sum of num_people from RSVPs)')
})

# Schema for creating an event
event_input_schema = api.model('EventInput', {
    'title': fields.String(required=True, description='Event title', min_length=3, max_length=150),
    'description': fields.String(description='Event description'),
    'category': fields.String(required=True, description='Event category', enum=['Garage Sales', 'Sports Matches', 'Community Classes', 'Volunteer Opportunities', 'Exhibitions', 'Small Festivals', 'Celebrations']),
    'start_datetime': fields.DateTime(dt_format='iso8601', required=True, description='Event start date and time (YYYY-MM-DDTHH:MM:SS)'),
    'end_datetime': fields.DateTime(dt_format='iso8601', description='Event end date and time (YYYY-MM-DDTHH:MM:SS)'),
    'location_address': fields.String(required=True, description='Event location')
})

# Schema for RSVPing to an event
rsvp_input_schema = api.model('RsvpInput', {
    'name': fields.String(description='Your name (if not logged in or for a guest)'),
    'email': fields.String(description='Your email (if not logged in or for a guest)'),
    'phone': fields.String(description='Your phone (if not logged in or for a guest)'),
    'num_people': fields.Integer(required=True, description='Number of people coming with you', default=1, min=1)
})

rsvp_output_schema = api.model('RsvpOutput', {
    'id': fields.Integer(readonly=True),
    'event_id': fields.Integer(),
    'user_id': fields.Integer(allow_null=True),
    'guest_name': fields.String(),
    'guest_email': fields.String(),
    'guest_phone': fields.String(),
    'num_people': fields.Integer(),
    'timestamp': fields.DateTime(dt_format='iso8601')
})