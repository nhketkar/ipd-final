from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, SelectField
from wtforms.validators import InputRequired, Length, NumberRange

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[InputRequired()])

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Password', validators=[InputRequired()])
    age = IntegerField('Age', validators=[NumberRange(min=18)])
    gender = SelectField('Gender', choices=[('Male', 'Male'), ('Female', 'Female')])

    # List of professions
    profession_choices = [
        ('Software Developer', 'Software Developer'),
        ('Doctor', 'Doctor'),
        ('Student','Student'),
        ('Teacher', 'Teacher'),
        ('Engineer', 'Engineer'),
        ('Artist', 'Artist'),
        ('Nurse', 'Nurse'),
        ('Lawyer', 'Lawyer'),
        ('Scientist', 'Scientist'),
        ('Businessperson', 'Businessperson'),
        ('Writer', 'Writer'),
        ('Other', 'Other')  # Other option
    ]
    profession = SelectField('Profession', choices=profession_choices, validators=[InputRequired()])
