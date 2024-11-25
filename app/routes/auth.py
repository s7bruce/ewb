from flask import Flask, render_template, request, redirect, Blueprint, url_for, flash
from app.models import db, User, vexrobots
from flask_login import login_user, login_required, logout_user
from werkzeug.security import check_password_hash

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/login', methods=['GET', 'POST'])
def login_post():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        print(f"Email: {email}, Password: {password}")

        user = User.query.filter_by(email=email).first()
        if not user:
            flash('Please check your login details and try again.')
            return redirect(url_for('auth.login'))
        elif not check_password_hash(user.password, password):
            flash('Please check your password and try again.')
            return redirect(url_for('auth.login'))
        else:
            login_user(user)
            print('logged in!')
            return redirect(url_for('routes_bp.profile'))
    user = request.form.get('user') 
    for user in user:
        print(f"User email: {user.email}")
    email = request.form.get('email')
    return redirect(url_for('main.profile')), user, email 

@auth.route('/profile')
@login_required
def profile():
    email = request.form.get('email')
    name = request.form.get('name')
    return render_template('profile.html', name=name, email=email)

@auth.route('/signup')
def signup():
    return render_template('signup.html')

@auth.route('/signup', methods=['GET', 'POST'])
def signup_post():
    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password') 

    if request.method == "GET":
        return render_template('login.html')
    
    user = User.query.filter_by(email=email).first() 

    if user: 
        flash('Email address already exists')
        return redirect(url_for('auth.signup'))

    new_user = User(email=email, name=name)
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
