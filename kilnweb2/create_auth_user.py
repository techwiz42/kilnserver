''' Add admin user '''
from kilnweb2 import app
from kilnweb2.model import User
from datetime import datetime

def add_admin_user():
    with app.app_context():
        username = input("Username? ")
        full_name = input("Full Name? ")
        email_address = input("Email Address? ")
        phone_number = input("Phone Number? ")
        password = input("Password? ")
        user = User(username, full_name, email_address, phone_number, "on", "on")
        user.set_password(password)
        app.db.session.add(user)
        app.db.session.commit()

if __name__ == '__main__':
  add_admin_user()
