from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.widgets import TextArea
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from flask_login import current_user
from kilnweb2.model import User, Job

# ...

class LoginForm(FlaskForm):
  username = StringField("User Name", validators = [DataRequired()])
  password = PasswordField('Password', validators = [DataRequired()])
  submit = SubmitField('Login')

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

class NewJobForm(FlaskForm):
  name = StringField("Job Name", validators=[DataRequired()])
  comment = TextAreaField('Comment')
  submit = SubmitField("Add Job")

  def validate_name(self, name):
    name = Job.query.filter_by(name=name.data).first()
    if name is not None:
      raise ValidationError('Please choose a different name for your job')
