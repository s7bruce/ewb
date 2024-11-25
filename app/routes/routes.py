from flask import Flask, render_template, request, redirect, Blueprint,jsonify
from app.models import db, vexrobots, User
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from sqlalchemy import func
from flask_login import login_manager, current_user, login_required

routes_bp = Blueprint(
    'routes_bp', __name__,
    template_folder='templates',
    static_folder='static')

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