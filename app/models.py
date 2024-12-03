from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy import desc
from sqlalchemy import create_engine, Column, DateTime, Integer, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class vexrobots(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    id = db.Column(db.Integer)
    kit = db.Column(db.Integer)
    kit_qty = db.Column(db.Integer)
    name = db.Column(db.String)
    cat = db.Column(db.String)
    sku = db.Column(db.String)
    desc = db.Column(db.String)
    price = db.Column(db.Float)

    def to_dict(self):
        return {
            "uid":self.uid,
            "id": self.id, 
            "kit": self.kit,
            "kit_qty": self.kit_qty,
            "name": self.name,
            "cat": self.cat,
            "sku": self.sku,
            "desc": self.desc,
            "price": self.price        
        }

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))

    def set_password(self, password):
       self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class file(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cust_name = db.Column(db.String)
    cust_unit = db.Column(db.Integer)

    def to_dict(self):
        return {
            "id":self.id,
            "cust_name":self.cust_name,
            "cust_unit":self.cust_unit
        }