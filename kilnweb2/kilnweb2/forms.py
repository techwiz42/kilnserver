''' The user-defined forms for this Flask app '''
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SubmitField, IntegerField, DecimalField, SelectField
from wtforms.validators import ValidationError, DataRequired, NumberRange, Email, EqualTo
from kilnweb2.model import User, Job

class LoginForm(FlaskForm):
    ''' The form that users login on '''
    username = StringField("User Name", validators = [DataRequired()])
    password = PasswordField('Password', validators = [DataRequired()])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    ''' The registration form for new users '''
    username = StringField('Username', validators=[DataRequired()])
    full_name = StringField("Full Name")
    phone_number = StringField("Phone Number")
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class PasswordResetForm(FlaskForm):
    ''' user can reset password '''
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class ShowUserForm(FlaskForm):
    ''' Display a user's data and allow him/her to edit '''
    full_name = StringField("Full Name")
    phone_number = StringField("Phone Number")
    email_address = StringField('Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Update User')

    def validate_username(self, username):
        ''' if can\'t find user, raise validation error '''
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        ''' if can\'t find user, raise validation error '''
        user = User.query.filter_by(email_address=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class NewJobForm(FlaskForm):
    ''' Form for entering a new job '''
    name = StringField("Job Name", validators=[DataRequired()])
    comment = TextAreaField('Comment')
    submit = SubmitField("Add Job")

    def validate_name(self, name):
        ''' if a job already exists with this name, raise validation error'''
        name = Job.query.filter_by(name=name.data).first()
        if name is not None:
            raise ValidationError('Please choose a different name for your job')

class SettingsForm(FlaskForm):
    erange = DecimalField("ERANGE", validators=[DataRequired()])
    drange = DecimalField("DRANGE", validators=[DataRequired()])
    interval = IntegerField("Interval", validators=[DataRequired()])
    units = SelectField("Units", choices = [("F", "Farenheidt"), ("C", "Centigrade")])
    submit = SubmitField("Save")
''' (c) Control Physics 2023, 2024 - all rights reserved '''
