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

class bindata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.String, default=0)
    trashcount = db.Column(db.Integer, default=0)
    weight = db.Column(db.Float, default=0)

    def to_dict(self):
        return {
            "id": self.id, 
            "Timestamp": self.timestamp,
            "Final Trash Count": self.trashcount,
            "Final Weight (g)": self.weight      
        }

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    # profilepic = db.Column(db.String)

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
    
class Bins(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    binNo = db.Column(db.Integer, unique=True, nullable=False)
    address = db.Column(db.String(200), nullable=True)
    picture = db.Column(db.LargeBinary, nullable=True)

    def __repr__(self):
        return f'<Bins {self.name}>'