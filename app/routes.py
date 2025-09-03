
from flask import Blueprint, render_template, redirect, url_for, flash
from .forms import SignupForm
from .models import User, db

# Create a Blueprint
main = Blueprint("main", __name__)

# Home route
@main.route("/")
def home():
    return render_template("home.html") 


# Signup for students only router
@main.route("/signup", methods=["GET", "POST"])
def signup():
    form = SignupForm()  

    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered!", "danger")
            return redirect(url_for("main.signup"))

     
        new_user = User(first_name=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully!", "success")
        return redirect(url_for("main.home"))

    return render_template("signup.html", form=form)


def register_routes(app):
    app.register_blueprint(main)
