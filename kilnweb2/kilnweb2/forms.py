from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from kilnweb2.model import User

# ...

class RegistrationForm(FlaskForm):
  username = StringField('Username', validators=[DataRequired()])
  full_name = StringField("Full Name") #FIXME: validate name & phone number?
  phone_number = StringField("Phone Number")
  email = StringField('Email', validators=[DataRequired(), Email()])
  password = PasswordField('Password', validators=[DataRequired()])
  password2 = PasswordField(
    'Repeat Password', validators=[DataRequired(), EqualTo('password')])
  submit = SubmitField('Register')

  def validate_username(self, username):
    user = User.query.filter_by(username=username.data).first()
    if user is not None:
      raise ValidationError('Please use a different username.')

  def validate_email(self, email):
    user = User.query.filter_by(email_address=email.data).first()
    if user is not None:
      raise ValidationError('Please use a different email address.')