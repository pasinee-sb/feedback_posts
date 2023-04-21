from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LogInForm, FeedbackForm
from sqlalchemy.exc import IntegrityError
import os
import re

app = Flask(__name__)
app.app_context().push()
uri = os.environ.get('DATABASE_URL', 'postgresql:///auth_exercise')

if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = os.environ.get('SECRET_KEY', 'hello!123')

# rest of connection code using the connection string `uri`
app.config["HEROKU_EXEC_DEBUG"] = os.environ.get('HEROKU_EXEC_DEBUG', '1')
print('###############')
print(app.config["SECRET_KEY"])
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config.update(SESSION_COOKIE_SAMESITE="None", SESSION_COOKIE_SECURE=True)

# connect to database
connect_db(app)

# create table in database
db.create_all()


@app.route('/')
def home():
    # check if someone is already logged in, redirect to user's page if so

    if "username" in session:
        return redirect(f"users/{session.get('username')}")
    return redirect('/register')


@app.route('/register', methods=['GET', 'POST'])
def register():

    form = RegisterForm()
    if form.validate_on_submit():

        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        new_user = User.register(username, password)

        user_info = User(username=username, password=new_user.password,
                         email=email, first_name=first_name, last_name=last_name)

        db.session.add(user_info)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('Username taken.  Please pick another')
            return render_template('register.html', form=form)

        session['username'] = user_info.username
        flash('Welcome! Successfully Created Your Account!', "success")
        return redirect(f"/users/{user_info.username}")

    return render_template('register.html', form=form)


@app.route('/secret')
def show_secret():

    if 'username' not in session:
        flash("Please log in", "danger")
        return redirect('/login')

    return render_template('secret.html')


@app.route('/login', methods=['GET', 'POST'])
def log_in():
    form = LogInForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)

        if user:
            flash(f"Welcome back, {user.username}", "success")
            session['username'] = user.username
            return redirect(f"/users/{user.username}")
        else:
            form.username.errors = ['Invalid username/password.']

    return render_template('login.html', form=form)


@app.route('/logout', methods=['POST'])
def log_out():

    session.pop('username')
    flash("Bye!")

    return redirect('/login')


@app.route('/users/<username>')
def show_info(username):
    # reveal personal info

    if "username" not in session:
        """check if anyone is logged in in session, send to log in page if none"""
        flash("Please login first!", "danger")
        return redirect('/login')
    # if session is not empty, get username for the person in session
    user_name = session.get('username')
    # get the person in session's info from database
    user_name_iden = User.query.filter_by(username=user_name).first()
    # get the person's info in the url /users/<username> from database
    user = User.query.filter_by(username=username).first()

    if user_name == user.username:
        """if person in session is the same person in the url then continue"""

        return render_template('showinfo.html', user=user)

    else:
        """flash error message and redirect to the person in session's own page"""
        flash("Secret is lock", "danger")
        return redirect(f"/users/{user_name_iden.username}")


@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    username = session.get('username')
    user = User.query.filter_by(username=username).first()

    if username == user.username:
        session.pop('username')
        db.session.delete(user)
        db.session.commit()
        return redirect("/")

    else:
        flash(f"You don't have the permission to delete")
        return redirect(f"/users/{user.username}")


@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def add_feedback(username):
    user_name = session.get('username')
    user = User.query.filter_by(username=username).first()

    # only user of current session can add feedback
    if user.username == user_name:
        form = FeedbackForm()

        # run validation for post request, ig it a post request
        if form.validate_on_submit():
            title = form.title.data
            content = form.content.data
            username = user_name

            new_feedback = Feedback(
                title=title, content=content, username=username)
            db.session.add(new_feedback)
            db.session.commit()
            flash('Feedback Created!', 'success')
            return redirect(f'/users/{new_feedback.username}')

        return render_template("feedback.html", form=form)
    flash("Please add feedback in your own log in", "danger")
    return redirect(f'/users/{user_name}/feedback/add')


@app.route('/feedback/<int:feedback_id>/update', methods=['GET', 'POST'])
def update_feedback(feedback_id):
    user_name = session.get('username')
    feedback = Feedback.query.get_or_404(feedback_id)
    user = feedback.username

    # only user of current session can update
    if user_name == user:

        # retrieve form and populate info from database, ready to be edited
        form = FeedbackForm(obj=feedback)
        """if it is a post request and token is valid, pull data from form, update to database and render home page"""
    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data

        db.session.commit()
        flash(f"Feedback is updated")
        return redirect(f"/users/{feedback.username}")
    return render_template("feedback.html", form=form)


@app.route('/feedback/<int:feedback_id>/delete', methods=['POST'])
def delete_feedback(feedback_id):
    user_name = session.get('username')
    feedback = Feedback.query.get_or_404(feedback_id)

    # only user of current session can delete

    if user_name == feedback.username:
        db.session.delete(feedback)
        db.session.commit()
        return redirect(f"/users/{user_name}")

    else:
        flash("You can't delete other people's feedback!", "danger")
        return redirect(f"/users/{user_name}")
