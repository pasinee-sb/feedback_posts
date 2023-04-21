from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField
from wtforms.validators import InputRequired, Email, Length


class RegisterForm(FlaskForm):
    username = StringField("username", validators=[
                           InputRequired(), Length(max=20)])
    password = PasswordField("password", validators=[InputRequired()])
    email = EmailField("email", validators=[InputRequired(), Length(max=50)])
    first_name = StringField("First Name", validators=[
                             InputRequired(), Length(max=50)])
    last_name = StringField("Last Name", validators=[
                            InputRequired(), Length(max=50)])


class LogInForm(FlaskForm):
    username = StringField("username", validators=[
                           InputRequired(), Length(max=20)])
    password = PasswordField("password", validators=[InputRequired()])


class FeedbackForm(FlaskForm):
    title = StringField("title", validators=[
        InputRequired(), Length(max=100)])
    content = StringField("content", validators=[
        InputRequired()])
