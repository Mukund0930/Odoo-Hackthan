from flask_restx import Api
from flask import Blueprint

# Create a Blueprint for the API.
# This allows for versioning or grouping under a common prefix like /api/v1
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Initialize Flask-RESTx Api with the blueprint
# Define authorisations for Swagger UI (JWT Bearer token)
authorizations = {
    'jwt': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': "Type in the *'Value'* input box below: **'Bearer <JWT>'**, where JWT is the token"
    }
}

api = Api(
    api_bp,
    version='1.0',
    title='Community Pulse API',
    description='API for the Community Pulse platform',
    doc='/doc', # URL for Swagger UI documentation
    authorizations=authorizations,
    security='jwt' # Default security scheme for all endpoints unless overridden
)

# Import namespaces here to register them with the API
# Import at the end to avoid circular dependencies
from .auth_api import ns as auth_ns
from .events_api import ns as events_ns
from .admin_api import ns as admin_ns

api.add_namespace(auth_ns, path='/auth')
api.add_namespace(events_ns, path='/events')
api.add_namespace(admin_ns, path='/admin')