from threading import Thread
from flask import render_template
from flask import current_app
from flask_mail import Message
from kilnweb2 import mail


def send_email(user):
    '''Send password reset link to user\'s email account'''
    token = user.get_reset_token()

    msg = Message()
    
    msg.sender = current_app.config['MAIL_USERNAME']
    msg.subject = "Kilnserver Password Reset"
    msg.recipients = [user.email_address]
    msg.html = render_template('reset_email.html', user=user, token=token)
    Thread(target=send, args=(msg)).start()

def send(msg):
    ''' Send email asynchronously '''
    with current_app.app_context():
        mail.send(msg)
