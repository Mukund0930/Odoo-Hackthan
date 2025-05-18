from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from . import db # db will be initialized in app/__init__.py

# Helper table for many-to-many relationship between users and events they are attending (RSVPs)
# Using an association object for RSVP to store extra data like num_people
class Rsvp(db.Model):
    __tablename__ = 'rsvps'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    guest_name = db.Column(db.String(100)) # For non-registered user RSVPs
    guest_email = db.Column(db.String(120)) # For non-registered user RSVPs
    guest_phone = db.Column(db.String(20))  # For non-registered user RSVPs
    num_people = db.Column(db.Integer, default=1, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', back_populates='rsvps')
    event = db.relationship('Event', back_populates='rsvps')

    def __repr__(self):
        return f'<Rsvp User: {self.user_id} Event: {self.event_id}>'

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(256)) # Increased length for stronger hashes
    is_admin = db.Column(db.Boolean, default=False)
    is_verified_organizer = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    # 'email', 'sms', 'whatsapp', 'none' or comma-separated for multiple
    notification_preference = db.Column(db.String(50), default='email')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationship to events organized by the user
    events_organized = db.relationship('Event', back_populates='organizer', lazy='dynamic', foreign_keys='Event.organizer_id')
    # Relationship to RSVPs made by the user
    rsvps = db.relationship('Rsvp', back_populates='user', lazy='dynamic', cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False) # e.g., "Garage Sales", "Sports Matches"
    start_datetime = db.Column(db.DateTime, nullable=False, index=True)
    end_datetime = db.Column(db.DateTime, nullable=True)
    location_address = db.Column(db.String(255), nullable=False)
    # latitude = db.Column(db.Float, nullable=True) # Add if doing geocoding
    # longitude = db.Column(db.Float, nullable=True) # Add if doing geocoding
    status = db.Column(db.String(20), default='PENDING', nullable=False) # PENDING, APPROVED, REJECTED, CANCELLED

    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    organizer = db.relationship('User', back_populates='events_organized')

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationship to users attending (via Rsvp association object)
    rsvps = db.relationship('Rsvp', back_populates='event', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Event {self.title}>'

    @property
    def attendees_count(self):
        return sum(rsvp.num_people for rsvp in self.rsvps)