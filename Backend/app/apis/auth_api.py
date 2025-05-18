from flask import request, current_app
from flask_restx import Namespace, Resource, fields
from ..models import User, db
from ..schemas.user_schemas import user_registration_schema, login_schema, token_schema, user_detail_schema
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from http import HTTPStatus

ns = Namespace('auth', description='Authentication related operations')

@ns.route('/register')
class UserRegistration(Resource):
    @ns.expect(user_registration_schema, validate=True)
    @ns.response(HTTPStatus.CREATED, 'User successfully registered.', token_schema)
    @ns.response(HTTPStatus.BAD_REQUEST, 'Validation error or user already exists.')
    def post(self):
        """Registers a new user."""
        data = ns.payload
        if User.query.filter((User.username == data['username']) | (User.email == data['email'])).first():
            return {'message': 'User with this username or email already exists'}, HTTPStatus.BAD_REQUEST

        new_user = User(
            username=data['username'],
            email=data['email'],
            phone_number=data.get('phone_number')
        )
        new_user.set_password(data['password'])
        db.session.add(new_user)
        db.session.commit()

        access_token = create_access_token(identity=new_user.id)
        return {'access_token': access_token}, HTTPStatus.CREATED

@ns.route('/login')
class UserLogin(Resource):
    @ns.expect(login_schema, validate=True)
    @ns.response(HTTPStatus.OK, 'Login successful.', token_schema)
    @ns.response(HTTPStatus.UNAUTHORIZED, 'Invalid credentials.')
    def post(self):
        """Logs in a user and returns an access token."""
        data = ns.payload
        email_or_username = data['email_or_username']
        password = data['password']

        user = User.query.filter((User.email == email_or_username) | (User.username == email_or_username)).first()

        if user and user.check_password(password):
            if user.is_banned:
                return {'message': 'This account has been banned.'}, HTTPStatus.UNAUTHORIZED
            access_token = create_access_token(identity=user.id)
            return {'access_token': access_token}, HTTPStatus.OK
        return {'message': 'Invalid email/username or password'}, HTTPStatus.UNAUTHORIZED

@ns.route('/me')
class Me(Resource):
    @jwt_required()
    @ns.doc(security='jwt') # Indicates this endpoint uses JWT security
    @ns.marshal_with(user_detail_schema)
    @ns.response(HTTPStatus.OK, 'Current user details.')
    @ns.response(HTTPStatus.UNAUTHORIZED, 'Token is missing or invalid.')
    def get(self):
        """Gets the current authenticated user's details."""
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return {'message': 'User not found'}, HTTPStatus.NOT_FOUND # Should not happen if token is valid
        return user, HTTPStatus.OK