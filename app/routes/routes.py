from flask import Flask, render_template, request, redirect, Blueprint, jsonify, flash, url_for, current_app, send_file, Response
from app.models import db, bindata, User, Bins
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
def get_bindata():
    binsdata = db.session.query(
        binsdata.id,
        binsdata.timestamp,
        binsdata.trashcount,
        binsdata.weight
    ).group_by(binsdata.id).all()
    
    bins_list = [{
        "id": binsdata.id,
        "timestamp": binsdata.timestamp,
        "trashcount": binsdata.trashcount,
        "weight": binsdata.weight
    } for binsdata in binsdata]
    return jsonify(bins_list)

@routes_bp.route('/inventory')
@login_required
def binsdata_page():
    bin = db.session.query(
        bindata.timestamp,
        bindata.trashcount,
        bindata.weight
    ).group_by(bindata.id).all()
    return render_template('inventory.html', bin=bin)

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
        existing_bin = db.session.query(bindata).first()
        
        if existing_bin:
            existing_bin.timestamp = row['Timestamp']
            existing_bin.trashcount = row['Final Trash Count']
            existing_bin.weight = row['Final Weight (g)']
        else:
            binsdata = bindata(
                timestamp=row['Timestamp'],
                trashcount=row['Final Trash Count'],
                weight=row['Final Weight (g)']
                
            )
            db.session.add(binsdata)
    db.session.commit()
    return redirect('/import')



@routes_bp.route("/bins", methods=['GET'])
@login_required
def bins():
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

@routes_bp.route('/bin_add', methods=['GET', 'POST'])
@login_required
def bin_add():
    if request.method == 'POST':
        # Retrieve form data
        name = request.form.get('name')
        binNo = request.form.get('binNo')
        address = request.form.get('address')

        # Retrieve the uploaded file
        picture = None
        file = request.files.get('picture')

        if file and allowed_file(file.filename):
            # Read the image file into memory and store as binary data
            img = Image.open(file.stream)  # Open the image from the stream
            img_byte_array = io.BytesIO()  # Create a byte array to hold the image data
            img.save(img_byte_array, format='PNG')  # Save image to byte array in PNG format
            picture = img_byte_array.getvalue()  # Get the binary data

        # Check if a customer with the same email already exists
        existing_bin = Bins.query.filter_by(address=address).first()
        if existing_bin:
            flash('A bin with this address already exists.', 'error')
            return redirect(url_for('routes_bp.customer_add'))

        # Create a new customer instance
        new_bin = Bins(
            name=name,
            binNo=binNo,
            address=address,
            picture=picture  # Store the image binary data in the DB
        )

        # Add to the database
        db.session.add(new_bin)
        db.session.commit()
        flash('Customer added successfully!', 'success')

        return redirect(url_for('routes_bp.bins'))

    return render_template('bin_add.html')

@routes_bp.route('/bin_edit/<int:id>', methods=['GET', 'POST'])
@login_required
def bin_edit(id):
    bin = Bins.query.get_or_404(id)
    
    if request.method == 'POST':
        # Retrieve form data
        bin.name = request.form.get('name')
        bin.binNo = request.form.get('binNo')
        bin.address = request.form.get('address')
        bin.picture = request.form.get('picture')

        # Retrieve and handle the profile picture if uploaded
        file = request.files.get('picture')

        if file and allowed_file(file.filename):
            # Read the image file into memory and store as binary data
            img = Image.open(file.stream)  # Open the image from the stream
            img_byte_array = io.BytesIO()  # Create a byte array to hold the image data
            img.save(img_byte_array, format='PNG')  # Save image to byte array in PNG format
            bin.picture = img_byte_array.getvalue()  # Update the binary data in the DB

        # Check if the new email is already taken by another customer
        if Bins.query.filter(bin.binNo == bin.binNo, bin.id != id).first():
            flash('This binNo is already associated with another bin.', 'error')
            return redirect(url_for('routes_bp.bin_edit', id=bin.id))

        # Commit the changes to the database
        db.session.commit()
        flash('Bin updated successfully!', 'success')

        return redirect(url_for('routes_bp.bin_detail', id=bin.id))

    return render_template('bin_edit.html', bin=bin)

@routes_bp.route('/bin_image/<int:id>')
def customer_image(id):
    bin = Bins.query.get(id)
    if bin and bin.picture:
        # Create a byte stream response with the binary data
        return Response(bin.picture, mimetype='image/png')
    return send_file('static/default_profile_picture.png', mimetype='image/png')  # Default image if none exists


@routes_bp.route('/bin_delete/<int:id>', methods=['POST'])
@login_required
def bin_delete(id):
    bin = Bins.query.get_or_404(id)
    db.session.delete(bin)
    db.session.commit()
    flash('Bin deleted successfully!', 'success')
    return redirect(url_for('routes_bp.bins'))