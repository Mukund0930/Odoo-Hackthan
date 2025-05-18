from flask_restx import Namespace, Resource
from flask_jwt_extended import jwt_required
from http import HTTPStatus

from ..models import db, Event, User
from ..schemas.event_schemas import event_output_schema
from ..schemas.user_schemas import user_detail_schema
from ..utils.decorators import admin_required
from ..services.notification_service import send_event_update_notification


ns = Namespace('admin', description='Admin-only operations')

@ns.route('/events/pending')
class AdminPendingEvents(Resource):
    @jwt_required()
    @admin_required
    @ns.doc(security='jwt')
    @ns.marshal_list_with(event_output_schema)
    def get(self):
        """Lists all events awaiting approval."""
        pending_events = Event.query.filter_by(status='PENDING').order_by(Event.created_at.desc()).all()
        return pending_events, HTTPStatus.OK

@ns.route('/events/<int:event_id>/approve')
class AdminApproveEvent(Resource):
    @jwt_required()
    @admin_required
    @ns.doc(security='jwt')
    @ns.response(HTTPStatus.OK, 'Event approved successfully.')
    @ns.response(HTTPStatus.NOT_FOUND, 'Event not found or already processed.')
    @ns.marshal_with(event_output_schema)
    def put(self, event_id):
        """Approves a pending event."""
        event = Event.query.filter_by(id=event_id, status='PENDING').first_or_404(
            description='Pending event not found or already processed.'
        )
        event.status = 'APPROVED'
        db.session.commit()
        # Optionally, notify organizer: send_event_update_notification(event, "Your event has been approved", event.organizer)
        return event, HTTPStatus.OK

@ns.route('/events/<int:event_id>/reject')
class AdminRejectEvent(Resource):
    @jwt_required()
    @admin_required
    @ns.doc(security='jwt')
    @ns.response(HTTPStatus.OK, 'Event rejected successfully.')
    @ns.response(HTTPStatus.NOT_FOUND, 'Event not found or already processed.')
    @ns.marshal_with(event_output_schema)
    def put(self, event_id):
        """Rejects a pending event."""
        event = Event.query.filter_by(id=event_id, status='PENDING').first_or_404(
            description='Pending event not found or already processed.'
        )
        event.status = 'REJECTED'
        db.session.commit()
        # Optionally, notify organizer: send_event_update_notification(event, "Your event has been rejected", event.organizer)
        return event, HTTPStatus.OK

@ns.route('/events/<int:event_id>/cancel') # Admin can cancel any event
class AdminCancelEvent(Resource):
    @jwt_required()
    @admin_required
    @ns.doc(security='jwt')
    @ns.response(HTTPStatus.OK, 'Event cancelled successfully.')
    @ns.response(HTTPStatus.NOT_FOUND, 'Event not found.')
    @ns.marshal_with(event_output_schema)
    def put(self, event_id):
        """Cancels an event (sets status to CANCELLED)."""
        event = Event.query.get_or_404(event_id)
        if event.status == 'CANCELLED':
            return {'message': 'Event is already cancelled.'}, HTTPStatus.BAD_REQUEST
        
        event.status = 'CANCELLED'
        db.session.commit()

        # Notify attendees
        for rsvp_entry in event.rsvps:
            recipient = rsvp_entry.user if rsvp_entry.user_id else rsvp_entry.guest_email
            if recipient:
                send_event_update_notification(event, "This event has been cancelled.", recipient)
        return event, HTTPStatus.OK

@ns.route('/users')
class AdminUserList(Resource):
    @jwt_required()
    @admin_required
    @ns.doc(security='jwt')
    @ns.marshal_list_with(user_detail_schema)
    def get(self):
        """Lists all users."""
        users = User.query.order_by(User.username).all()
        return users, HTTPStatus.OK

@ns.route('/users/<int:user_id>/verify-organizer')
class AdminVerifyOrganizer(Resource):
    @jwt_required()
    @admin_required
    @ns.doc(security='jwt')
    @ns.response(HTTPStatus.OK, 'User organizer status updated.')
    @ns.response(HTTPStatus.NOT_FOUND, 'User not found.')
    @ns.marshal_with(user_detail_schema)
    def put(self, user_id):
        """Toggles the 'is_verified_organizer' status for a user."""
        user = User.query.get_or_404(user_id)
        user.is_verified_organizer = not user.is_verified_organizer
        db.session.commit()
        return user, HTTPStatus.OK

@ns.route('/users/<int:user_id>/ban')
class AdminBanUser(Resource):
    @jwt_required()
    @admin_required
    @ns.doc(security='jwt')
    @ns.response(HTTPStatus.OK, 'User ban status updated.')
    @ns.response(HTTPStatus.NOT_FOUND, 'User not found.')
    @ns.marshal_with(user_detail_schema)
    def put(self, user_id):
        """Toggles the 'is_banned' status for a user."""
        user = User.query.get_or_404(user_id)
        if user.is_admin: # Prevent banning other admins through this endpoint
            return {'message': 'Cannot ban an admin user.'}, HTTPStatus.FORBIDDEN
        user.is_banned = not user.is_banned
        db.session.commit()
        return user, HTTPStatus.OK