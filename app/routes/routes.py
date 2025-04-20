from flask import Flask, render_template, request, redirect, Blueprint, jsonify, flash, url_for, current_app, send_file, Response
from app.models import db, vexrobots, User, Bins
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from sqlalchemy import func
from flask_login import login_manager, current_user, login_required
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from PIL import Image
import io

routes_bp = Blueprint(
    'routes_bp', __name__,
    template_folder='templates',
    static_folder='static')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@routes_bp.route('/')
def login():
    return render_template('login.html')

@routes_bp.route('/index')
@login_required
def index():
    return render_template('index.html')

@routes_bp.route('/prices')
@login_required
def prices():
    return render_template('prices.html')

@routes_bp.route('/profile')
@login_required
def profile():
    user = User.query.filter_by(id=current_user.id).first()
    email = user.email
    name = user.name
    return render_template('profile.html', email=email, name=name)

# @routes_bp.route('/profilev2')
# @login_required
# def profilev2():
#     user = User.query.filter_by(id=current_user.id).first()
#     email = user.email
#     name = user.name
#     profilepic = user.profilepic
#     return render_template('profilev2.html',email=email,name=name,profilepic=profilepic)

@routes_bp.route('/api/inventory')
@login_required
def get_vexrobots():
    robots = db.session.query(
        vexrobots.id,
        vexrobots.name,
        vexrobots.sku,
        vexrobots.desc,
        vexrobots.kit,
        vexrobots.kit_qty,
        vexrobots.price,
        func.count(vexrobots.kit_qty).label('total_kit_qty'),
        func.count(vexrobots.id).label('total_db_qty')
    ).group_by(vexrobots.id, vexrobots.name, vexrobots.sku, vexrobots.desc, vexrobots.kit, vexrobots.kit_qty, vexrobots.price).all()
    
    robots_list = [{
        "id": robot.id,
        "name": robot.name,
        "sku": robot.sku,
        "desc": robot.desc,
        "kit": robot.kit,
        "kit_qty": robot.kit_qty,
        "price": robot.price,
        "total_kit_qty": robot.total_kit_qty,
        "total_db_qty": robot.total_db_qty
    } for robot in robots]
    return jsonify(robots_list)

@routes_bp.route('/inventory')
@login_required
def vexrobots_page():
    return render_template('inventory.html')

@routes_bp.route("/import")
@login_required
def importcsv():
  title = "Import Data"
  return render_template("importcsv.html", title=title)

@routes_bp.route("/import/submit", methods=["POST"])
@login_required
def submit():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        uploaded_file.save(uploaded_file.filename)
        parse_csv(uploaded_file.filename)
        
    return redirect('/import')

def parse_csv(file_path):
    csv_data = pd.read_csv(file_path)

    for i, row in csv_data.iterrows():
        existing_robot = db.session.query(vexrobots).filter_by(uid=row['uid']).first()
        
        if existing_robot:
            existing_robot.id = row['id']
            existing_robot.kit = row['kit']
            existing_robot.kit_qty = row['kit qty']
            existing_robot.name = row['name']
            existing_robot.cat = row['category']
            existing_robot.sku = row['sku']
            existing_robot.desc = row['desc']
            existing_robot.price = row['price']
        else:
            robot = vexrobots(
                uid=row['uid'],
                id=row['id'], 
                kit=row['kit'], 
                kit_qty=row['kit qty'], 
                name=row['name'], 
                cat=row['category'], 
                sku=row['sku'],
                desc=row['desc'],
                price=row['price']
            )
            db.session.add(robot)
    db.session.commit()
    return redirect('/import')



@routes_bp.route("/bins", methods=['GET'])
@login_required
def customers():
    search_term = request.args.get('search', '', type=str)
    query = Bins.query
    if search_term:
        query = query.filter(
            Bins.name.ilike(f'%{search_term}%'),
            Bins.name.ilike(f'%{search_term}%')
        )

    bins = query.all()

    return render_template("bins.html", bins=bins, search_term=search_term)

@routes_bp.route('/bins/<int:id>', methods=['GET'])
@login_required
def bin_detail(id):
    bin = Bins.query.get_or_404(id)
    return render_template('bin_detail.html', bin=bin)

@routes_bp.route('/customer_add', methods=['GET', 'POST'])
@login_required
def customer_add():
    if request.method == 'POST':
        # Retrieve form data
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')

        # Retrieve the uploaded file
        profile_picture = None
        file = request.files.get('profile_picture')

        if file and allowed_file(file.filename):
            # Read the image file into memory and store as binary data
            img = Image.open(file.stream)  # Open the image from the stream
            img_byte_array = io.BytesIO()  # Create a byte array to hold the image data
            img.save(img_byte_array, format='PNG')  # Save image to byte array in PNG format
            profile_picture = img_byte_array.getvalue()  # Get the binary data

        # Check if a customer with the same email already exists
        existing_customer = Customer.query.filter_by(email=email).first()
        if existing_customer:
            flash('A customer with this email already exists.', 'error')
            return redirect(url_for('routes_bp.customer_add'))

        # Create a new customer instance
        new_cust = Customer(
            name=name,
            email=email,
            phone=phone,
            address=address,
            profile_picture=profile_picture  # Store the image binary data in the DB
        )

        # Add to the database
        db.session.add(new_cust)
        db.session.commit()
        flash('Customer added successfully!', 'success')

        return redirect(url_for('routes_bp.customers'))

    return render_template('customer_add.html')

@routes_bp.route('/customer_edit/<int:id>', methods=['GET', 'POST'])
@login_required
def customer_edit(id):
    customer = Customer.query.get_or_404(id)
    
    if request.method == 'POST':
        # Retrieve form data
        customer.name = request.form.get('name')
        customer.email = request.form.get('email')
        customer.phone = request.form.get('phone')
        customer.address = request.form.get('address')

        # Retrieve and handle the profile picture if uploaded
        file = request.files.get('profile_picture')

        if file and allowed_file(file.filename):
            # Read the image file into memory and store as binary data
            img = Image.open(file.stream)  # Open the image from the stream
            img_byte_array = io.BytesIO()  # Create a byte array to hold the image data
            img.save(img_byte_array, format='PNG')  # Save image to byte array in PNG format
            customer.profile_picture = img_byte_array.getvalue()  # Update the binary data in the DB

        # Check if the new email is already taken by another customer
        if Customer.query.filter(Customer.email == customer.email, Customer.id != id).first():
            flash('This email is already associated with another customer.', 'error')
            return redirect(url_for('routes_bp.customer_edit', id=customer.id))

        # Commit the changes to the database
        db.session.commit()
        flash('Customer updated successfully!', 'success')

        return redirect(url_for('routes_bp.customer_detail', id=customer.id))

    return render_template('customer_edit.html', customer=customer)

@routes_bp.route('/customer_image/<int:id>')
def customer_image(id):
    customer = Customer.query.get(id)
    if customer and customer.profile_picture:
        # Create a byte stream response with the binary data
        return Response(customer.profile_picture, mimetype='image/png')
    return send_file('static/default_profile_picture.png', mimetype='image/png')  # Default image if none exists