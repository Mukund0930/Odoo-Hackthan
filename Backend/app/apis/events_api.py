from flask_restx import Namespace, Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from http import HTTPStatus
from datetime import datetime, timezone

from ..models import db, Event, User, Rsvp
from ..schemas.event_schemas import event_input_schema, event_output_schema, rsvp_input_schema, rsvp_output_schema
from ..utils.decorators import event_organizer_or_admin_required
from ..services.notification_service import send_event_update_notification

ns = Namespace('events', description='Event related operations')

# Parser for query parameters for GET /events
event_query_parser = reqparse.RequestParser()
event_query_parser.add_argument('category', type=str, help='Filter by category')
event_query_parser.add_argument('location', type=str, help='Filter by location (text search on address)') # Simple text search
event_query_parser.add_argument('date_from', type=str, help='Filter events starting from this date (YYYY-MM-DD)')
event_query_parser.add_argument('date_to', type=str, help='Filter events starting up to this date (YYYY-MM-DD)')
event_query_parser.add_argument('page', type=int, default=1, help='Page number')
event_query_parser.add_argument('per_page', type=int, default=10, help='Items per page')


@ns.route('')
class EventList(Resource):
    @ns.expect(event_query_parser)
    @ns.marshal_list_with(event_output_schema)
    def get(self):
        """Browse approved events (paginated and filterable)."""
        args = event_query_parser.parse_args()
        query = Event.query.filter_by(status='APPROVED').order_by(Event.start_datetime.asc())

        if args.get('category'):
            query = query.filter(Event.category.ilike(f"%{args['category']}%"))
        if args.get('location'):
            query = query.filter(Event.location_address.ilike(f"%{args['location']}%"))
        if args.get('date_from'):
            try:
                date_from_dt = datetime.strptime(args['date_from'], '%Y-%m-%d').replace(tzinfo=timezone.utc)
                query = query.filter(Event.start_datetime >= date_from_dt)
            except ValueError:
                return {"message": "Invalid date_from format. Use YYYY-MM-DD."}, HTTPStatus.BAD_REQUEST
        if args.get('date_to'):
            try:
                # Include events that start on date_to
                date_to_dt = datetime.strptime(args['date_to'] + " 23:59:59", '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
                query = query.filter(Event.start_datetime <= date_to_dt)
            except ValueError:
                return {"message": "Invalid date_to format. Use YYYY-MM-DD."}, HTTPStatus.BAD_REQUEST

        page = args.get('page', 1)
        per_page = args.get('per_page', 10)
        paginated_events = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return paginated_events.items, HTTPStatus.OK

    @jwt_required()
    @ns.doc(security='jwt')
    @ns.expect(event_input_schema, validate=True)
    @ns.marshal_with(event_output_schema, code=HTTPStatus.CREATED)
    @ns.response(HTTPStatus.UNAUTHORIZED, 'Token is missing or invalid.')
    @ns.response(HTTPStatus.BAD_REQUEST, 'Validation error.')
    def post(self):
        """Creates a new event (status will be PENDING)."""
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or user.is_banned:
            return {'message': 'User not authorized or banned.'}, HTTPStatus.UNAUTHORIZED

        data = ns.payload
        try:
            start_datetime = datetime.fromisoformat(data['start_datetime'])
            end_datetime = datetime.fromisoformat(data['end_datetime']) if data.get('end_datetime') else None
        except ValueError:
            return {'message': 'Invalid datetime format. Use ISO 8601 (YYYY-MM-DDTHH:MM:SS).'}, HTTPStatus.BAD_REQUEST

        if end_datetime and end_datetime < start_datetime:
            return {'message': 'End datetime cannot be before start datetime.'}, HTTPStatus.BAD_REQUEST

        new_event = Event(
            title=data['title'],
            description=data.get('description'),
            category=data['category'],
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            location_address=data['location_address'],
            organizer_id=current_user_id,
            status='PENDING' # Events need approval by default
        )
        db.session.add(new_event)
        db.session.commit()
        return new_event, HTTPStatus.CREATED

@ns.route('/<int:event_id>')
@ns.response(HTTPStatus.NOT_FOUND, 'Event not found.')
class EventItem(Resource):
    @ns.marshal_with(event_output_schema)
    def get(self, event_id):
        """Gets details of a specific approved event."""
        event = Event.query.filter_by(id=event_id, status='APPROVED').first()
        if not event:
            # Also check if it's pending and the user is the organizer or admin
            event_pending = Event.query.get(event_id)
            if event_pending and event_pending.status == 'PENDING':
                try: # check if token is present, optional for this part
                    current_user_id = get_jwt_identity()
                    user = User.query.get(current_user_id)
                    if user and (user.id == event_pending.organizer_id or user.is_admin):
                        return event_pending, HTTPStatus.OK
                except Exception: # No JWT or invalid
                    pass
            return {'message': 'Approved event not found or you do not have permission to view.'}, HTTPStatus.NOT_FOUND
        return event, HTTPStatus.OK

    @jwt_required()
    @ns.doc(security='jwt')
    @event_organizer_or_admin_required(event_id_param_name='event_id')
    @ns.expect(event_input_schema, validate=True) # Re-use input schema for updates
    @ns.marshal_with(event_output_schema)
    @ns.response(HTTPStatus.FORBIDDEN, 'Permission denied.')
    def put(self, event_id):
        """Updates an event (organizer or admin only)."""
        event = Event.query.get_or_404(event_id)
        data = ns.payload

        try:
            start_datetime = datetime.fromisoformat(data['start_datetime']) if data.get('start_datetime') else event.start_datetime
            end_datetime = datetime.fromisoformat(data['end_datetime']) if data.get('end_datetime') else event.end_datetime
        except ValueError:
            return {'message': 'Invalid datetime format. Use ISO 8601 (YYYY-MM-DDTHH:MM:SS).'}, HTTPStatus.BAD_REQUEST
        
        if end_datetime and start_datetime and end_datetime < start_datetime:
             return {'message': 'End datetime cannot be before start datetime.'}, HTTPStatus.BAD_REQUEST

        original_location = event.location_address
        original_start_time = event.start_datetime

        event.title = data.get('title', event.title)
        event.description = data.get('description', event.description)
        event.category = data.get('category', event.category)
        event.start_datetime = start_datetime
        event.end_datetime = end_datetime
        event.location_address = data.get('location_address', event.location_address)
        
        # If critical info changed, set status to PENDING for re-approval, unless an admin is editing
        current_user_id = get_jwt_identity()
        editor = User.query.get(current_user_id)
        if not editor.is_admin and (event.location_address != original_location or event.start_datetime != original_start_time):
            event.status = 'PENDING' # Needs re-approval if organizer changes critical details

        db.session.commit()

        # Notify attendees if APPROVED event details changed
        if event.status == 'APPROVED' and (event.location_address != original_location or event.start_datetime != original_start_time):
            update_message = []
            if event.location_address != original_location:
                update_message.append(f"Location changed to: {event.location_address}")
            if event.start_datetime != original_start_time:
                update_message.append(f"Start time changed to: {event.start_datetime.strftime('%Y-%m-%d %I:%M %p')}")

            if update_message:
                full_update_message = ". ".join(update_message)
                for rsvp_entry in event.rsvps:
                    recipient = rsvp_entry.user if rsvp_entry.user_id else rsvp_entry.guest_email
                    if recipient:
                        send_event_update_notification(event, full_update_message, recipient)
        
        return event, HTTPStatus.OK

    @jwt_required()
    @ns.doc(security='jwt')
    @event_organizer_or_admin_required(event_id_param_name='event_id')
    @ns.response(HTTPStatus.NO_CONTENT, 'Event successfully deleted.')
    @ns.response(HTTPStatus.FORBIDDEN, 'Permission denied.')
    def delete(self, event_id):
        """Deletes an event (organizer or admin only)."""
        event = Event.query.get_or_404(event_id)
        db.session.delete(event)
        db.session.commit()
        return '', HTTPStatus.NO_CONTENT


@ns.route('/<int:event_id>/rsvp')
class EventRsvp(Resource):

    @jwt_required(optional=True)  # Allow non-logged-in users if guest details are provided
    @ns.doc(security='jwt')
    @ns.expect(rsvp_input_schema, validate=True)
    @ns.marshal_with(rsvp_output_schema, code=HTTPStatus.CREATED)
    @ns.response(HTTPStatus.NOT_FOUND, 'Event not found or not approved.')
    @ns.response(HTTPStatus.BAD_REQUEST, 'Validation error or already RSVPd.')
    @ns.response(HTTPStatus.UNAUTHORIZED, 'Guest details required if not logged in.')
    def post(self, event_id):
        """Mark interest (RSVP) for an event."""
        event = Event.query.filter_by(id=event_id, status='APPROVED').first_or_404(
            description='Event not found or not approved for RSVPs.'
        )

        data = ns.payload
        current_user_id = get_jwt_identity()

        user_id_for_rsvp = None
        guest_name = data.get('name')
        guest_email = data.get('email')
        guest_phone = data.get('phone')
        num_people = data.get('num_people', 1)

        if current_user_id:
            user = User.query.get(current_user_id)
            if not user or user.is_banned:
                return {'message': 'User not authorized or banned.'}, HTTPStatus.UNAUTHORIZED

            user_id_for_rsvp = user.id

            existing_rsvp = Rsvp.query.filter_by(
                event_id=event.id,
                user_id=user.id
            ).first()
            if existing_rsvp:
                return {'message': 'You have already RSVPd to this event.'}, HTTPStatus.BAD_REQUEST

        else:
            if not guest_name or not guest_email:
                return {
                    'message': 'Name and Email are required for guest RSVPs.'
                }, HTTPStatus.UNAUTHORIZED

            existing_guest_rsvp = Rsvp.query.filter_by(
                event_id=event.id,
                guest_email=guest_email,
                user_id=None
            ).first()
            if existing_guest_rsvp:
                return {
                    'message': f'Guest with email {guest_email} has already RSVPd to this event.'
                }, HTTPStatus.BAD_REQUEST

        rsvp = Rsvp(
                 event_id=event.id,
                 user_id=user_id_for_rsvp,
                 guest_name=guest_name,
                 guest_email=guest_email,
                guest_phone=guest_phone,
                num_people=num_people
                            )
        

        db.session.add(rsvp)
        db.session.commit()
        return rsvp, HTTPStatus.CREATED

    @jwt_required(optional=True) # Check if user is logged in, otherwise not applicable
    @ns.doc(security='jwt')
    @ns.response(HTTPStatus.NO_CONTENT, 'RSVP successfully removed.')
    @ns.response(HTTPStatus.NOT_FOUND, 'RSVP not found or event not found.')
    @ns.response(HTTPStatus.UNAUTHORIZED, 'Guest email required to cancel guest RSVP if not logged in.')
    def delete(self, event_id):
        """Removes user's or guest's RSVP from an event."""
        event = Event.query.get_or_404(event_id)
        current_user_id = get_jwt_identity()

        if current_user_id:
            user = User.query.get(current_user_id)
            if not user: return {'message': 'User not found'}, HTTPStatus.UNAUTHORIZED # Should not happen
            
            rsvp_to_delete = Rsvp.query.filter_by(event_id=event.id, user_id=user.id).first()
            if not rsvp_to_delete:
                return {'message': 'RSVP not found for this user and event.'}, HTTPStatus.NOT_FOUND
        else: # Guest trying to cancel
            guest_email_param = ns.parser().add_argument('guest_email', type=str, required=True, help='Guest email for RSVP cancellation', location='args').parse_args()
            guest_email = guest_email_param.get('guest_email')
            if not guest_email:
                return {'message': 'Guest email is required to cancel a guest RSVP.'}, HTTPStatus.UNAUTHORIZED

            rsvp_to_delete = Rsvp.query.filter_by(event_id=event.id, guest_email=guest_email, user_id=None).first()
            if not rsvp_to_delete:
                return {'message': f'RSVP not found for guest email {guest_email} and event.'}, HTTPStatus.NOT_FOUND
        
        db.session.delete(rsvp_to_delete)
        db.session.commit()
        return '', HTTPStatus.NO_CONTENT


@ns.route('/<int:event_id>/rsvps')
@ns.response(HTTPStatus.NOT_FOUND, 'Event not found.')
class EventRsvpList(Resource):
    @jwt_required()
    @ns.doc(security='jwt')
    @event_organizer_or_admin_required(event_id_param_name='event_id') # Only organizer or admin can see
    @ns.marshal_list_with(rsvp_output_schema)
    def get(self, event_id):
        """Lists all RSVPs for a specific event (organizer/admin only)."""
        event = Event.query.get_or_404(event_id)
        return event.rsvps.all(), HTTPStatus.OK


@ns.route('/my-organized-events')
class MyOrganizedEvents(Resource):
    @jwt_required()
    @ns.doc(security='jwt')
    @ns.marshal_list_with(event_output_schema)
    def get(self):
        """Gets all events organized by the current user."""
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)
        # Shows all statuses for organizer's own events
        events = Event.query.filter_by(organizer_id=user.id).order_by(Event.start_datetime.desc()).all()
        return events, HTTPStatus.OK

@ns.route('/my-rsvps')
class MyRsvps(Resource):
    @jwt_required()
    @ns.doc(security='jwt')
    @ns.marshal_list_with(event_output_schema) # We want to show event details for RSVPd events
    def get(self):
        """Gets all events the current user has RSVPd to."""
        current_user_id = get_jwt_identity()
        user = User.query.get_or_404(current_user_id)
        
        # Get events based on user's RSVPs
        events = Event.query.join(Rsvp).filter(Rsvp.user_id == user.id, Event.status == 'APPROVED').order_by(Event.start_datetime.asc()).all()
        return events, HTTPStatus.OK