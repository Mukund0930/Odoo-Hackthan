from flask_restx import fields
from ..apis import api # Import the api object from apis/__init__.py

user_public_schema = api.model('UserPublic', {
    'id': fields.Integer(readonly=True, description='The user unique identifier'),
    'username': fields.String(required=True, description='Username'),
    'is_verified_organizer': fields.Boolean(description='Is the user a verified organizer')
})

user_detail_schema = api.model('UserDetail', {
    'id': fields.Integer(readonly=True),
    'username': fields.String(required=True),
    'email': fields.String(required=True),
    'phone_number': fields.String(),
    'is_admin': fields.Boolean(),
    'is_verified_organizer': fields.Boolean(),
    'is_banned': fields.Boolean(),
    'notification_preference': fields.String(),
    'created_at': fields.DateTime(dt_format='iso8601')
})

user_registration_schema = api.model('UserRegistration', {
    'username': fields.String(required=True, description='Username', min_length=3),
    'email': fields.String(required=True, description='User email', pattern=r"[^@]+@[^@]+\.[^@]+"),
    'password': fields.String(required=True, description='User password', min_length=6),
    'phone_number': fields.String(description='User phone number (optional)')
})

login_schema = api.model('Login', {
    'email_or_username': fields.String(required=True, description='Email or Username'),
    'password': fields.String(required=True, description='Password')
})

token_schema = api.model('Token', {
    'access_token': fields.String(description='Access Token for authentication')
})