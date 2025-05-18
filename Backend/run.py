import os
from app import create_app, db # db might be needed for initial setup or commands
from app.models import User, Event, Rsvp # To make them available for flask shell etc.

# Determine the config name from environment or default to 'development'
config_name = os.getenv('FLASK_ENV') or 'default'
app = create_app(config_name)

# You can add CLI commands here if needed using app.cli.command()
# Example: a command to create an admin user
@app.cli.command("create-admin")
def create_admin():
    """Creates a default admin user."""
    from getpass import getpass
    username = input("Enter admin username: ")
    email = input("Enter admin email: ")
    password = getpass("Enter admin password: ")
    confirm_password = getpass("Confirm admin password: ")

    if password != confirm_password:
        print("Passwords do not match.")
        return

    if User.query.filter_by(email=email).first():
        print(f"User with email {email} already exists.")
        return
    if User.query.filter_by(username=username).first():
        print(f"User with username {username} already exists.")
        return

    admin_user = User(username=username, email=email, is_admin=True)
    admin_user.set_password(password)
    db.session.add(admin_user)
    db.session.commit()
    print(f"Admin user {username} created successfully.")


if __name__ == '__main__':
    app.run(debug=app.config.get('DEBUG', False), host='0.0.0.0', port=5000)