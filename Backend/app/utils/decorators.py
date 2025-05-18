from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask import jsonify
from http import HTTPStatus
from ..models import User

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if user and user.is_admin:
            return fn(*args, **kwargs)
        else:
            return {'message': 'Admins only!'}, HTTPStatus.FORBIDDEN
    return wrapper

def verified_organizer_or_admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if user and (user.is_admin or user.is_verified_organizer):
            return fn(*args, **kwargs)
        else:
            return {'message': 'Verified organizers or admins only!'}, HTTPStatus.FORBIDDEN
    return wrapper

# You might also want a decorator to check if the current user is the event organizer
def event_organizer_or_admin_required(event_id_param_name='event_id'):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from ..models import Event # Local import to avoid circular dependency
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            event_id = kwargs.get(event_id_param_name)
            if not event_id:
                return {'message': 'Event ID not found in request path.'}, HTTPStatus.BAD_REQUEST

            event = Event.query.get(event_id)
            if not event:
                return {'message': 'Event not found.'}, HTTPStatus.NOT_FOUND

            if user and (user.is_admin or event.organizer_id == user.id):
                return fn(*args, **kwargs)
            else:
                return {'message': 'Permission denied. Must be event organizer or admin.'}, HTTPStatus.FORBIDDEN
        return wrapper
    return decorator