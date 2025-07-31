import os
import csv
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from functools import wraps
import random
from datetime import datetime, timedelta
from flask import send_from_directory
from flask_sqlalchemy import SQLAlchemy
import json
from werkzeug.security import generate_password_hash, check_password_hash # Import for password hashing

app = Flask(__name__, static_folder='static')
app.secret_key = 'ongc_secret_key_2025'

# Configure Database Connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/ongc_users_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define User model (from previous step)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False) # Store hashed passwords
    department = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), default='user')

    def __repr__(self):
        return f'<User {self.email}>'

# Define Well model (from previous step)
class Well(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    field_name = db.Column(db.String(50), nullable=False)
    well_id = db.Column(db.String(50), nullable=False)
    fthp = db.Column(db.Float, nullable=True)
    qg = db.Column(db.Float, nullable=True)
    qw = db.Column(db.Float, nullable=True)
    qc = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(50), nullable=False)
    operator = db.Column(db.String(100), nullable=True)
    depth = db.Column(db.String(50), nullable=True)
    reservoir = db.Column(db.String(100), nullable=True)
    completion_date = db.Column(db.Date, nullable=True)
    last_maintenance = db.Column(db.Date, nullable=True)
    last_inspection = db.Column(db.Date, nullable=True)
    next_scheduled = db.Column(db.String(50), nullable=True) # Can be date or 'N/A'
    uptime = db.Column(db.String(10), nullable=True)
    workover_history = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    recent_operations_json = db.Column(db.Text, nullable=True) # Storing JSON string

    def __repr__(self):
        return f'<Well {self.field_name}-{self.well_id}>'

    # Helper to get recent_operations as a list
    @property
    def recent_operations(self):
        if self.recent_operations_json:
            return json.loads(self.recent_operations_json)
        return []

    # Helper to set recent_operations from a list
    @recent_operations.setter
    def recent_operations(self, value):
        self.recent_operations_json = json.dumps(value)


# Create tables if they don't exist
with app.app_context():
    db.create_all()

# Initial user data for first run (if users table is empty)
# This will create an admin user on first run if the users table is empty
with app.app_context():
    if User.query.first() is None:
        admin_user = User(
            name="Admin User",
            email="admin@ongc.co.in",
            password=generate_password_hash("securepassword"), # Hashing the password
            department="IT",
            role="admin"
        )
        engineer_user = User(
            name="Field Engineer",
            email="engineer@ongc.co.in",
            password=generate_password_hash("ongc1234"), # Hashing the password
            department="Operations",
            role="user"
        )
        db.session.add(admin_user)
        db.session.add(engineer_user)
        db.session.commit()
        print("Initial user data populated into the database.")

# Initial well data population (from previous step)
def populate_wells_from_initial_data():
    # Define your initial WELL_DETAILS and CSV_DATA here if you want to use them
    # to populate the database on first run.
    # This data was previously in app.py, copy it here for initial population.
    WELL_DETAILS = {
        # Agartala Field
        "Agartala-A#1": {
            "operator": "ONGC",
            "depth": "3500m",
            "reservoir": "Tipam Formation",
            "completion_date": "2015-08-12",
            "last_maintenance": "2025-05-18",
            "last_inspection": "2025-06-05",
            "next_scheduled": "2025-07-10",
            "uptime": "98.7%",
            "workover_history": "3 times",
            "description": "Primary production well in Agartala field. Consistently performing above expectations with minimal maintenance required. Equipped with advanced monitoring sensors.",
            "recent_operations": [
                "Monthly pressure survey completed on 2025-05-15",
                "Choke size adjusted to 32/64\" on 2025-04-22",
                "Chemical treatment for corrosion prevention applied on 2025-04-10",
                "Downhole pressure gauge replaced on 2025-03-28",
                "Production test conducted on 2025-02-15"
            ]
        },
        "Agartala-A#2": {
            "operator": "ONGC",
            "depth": "3420m",
            "reservoir": "Tipam Formation",
            "completion_date": "2016-02-18",
            "last_maintenance": "2025-01-15",
            "last_inspection": "2025-02-20",
            "next_scheduled": "2025-08-15",
            "uptime": "97.2%",
            "workover_history": "2 times",
            "description": "High-productivity well with occasional sand production issues. Equipped with desander and requires frequent monitoring.",
            "recent_operations": [
                "Sand management system inspected on 2025-04-10",
                "Choke size increased to 36/64\" on 2025-03-28",
                "Downhole pressure survey completed on 2025-03-05",
                "Production logging test conducted on 2025-02-15",
                "Chemical injection system serviced on 2025-01-20"
            ]
        },
        "Agartala-A#3": {
            "operator": "ONGC",
            "depth": "3650m",
            "reservoir": "Tipam Formation",
            "completion_date": "2017-05-22",
            "last_maintenance": "2025-04-10",
            "last_inspection": "2025-05-12",
            "next_scheduled": "2025-09-15",
            "uptime": "99.1%",
            "workover_history": "1 time",
            "description": "Deep gas well with high pressure. Requires regular monitoring of casing pressure and temperature.",
            "recent_operations": [
                "Casing pressure monitoring system upgraded on 2025-05-05",
                "Temperature sensors calibrated on 2025-04-18",
                "Safety valve tested on 2025-03-25",
                "Production optimization completed on 2025-02-28",
                "Chemical treatment applied on 2025-01-10"
            ]
        },
        "Agartala-A#4": {
            "operator": "ONGC",
            "depth": "3300m",
            "reservoir": "Tipam Formation",
            "completion_date": "2014-11-30",
            "last_maintenance": "2023-08-15",
            "last_inspection": "2023-09-10",
            "next_scheduled": "N/A",
            "uptime": "0%",
            "workover_history": "4 times",
            "description": "Abandoned due to depleted reserves. Well was plugged and abandoned in 2024. Site secured and marked for future re-entry possibilities.",
            "recent_operations": [
                "Final abandonment completed on 2024-01-15",
                "Cement plug set at 3200m on 2023-12-20",
                "Wellhead removed and capped on 2023-11-10",
                "Environmental assessment completed on 2023-10-05",
                "Final production test conducted on 2023-09-15"
            ]
        },
        "Agartala-A#5": {
            "operator": "ONGC",
            "depth": "3550m",
            "reservoir": "Tipam Formation",
            "completion_date": "2018-03-14",
            "last_maintenance": "2025-05-18",
            "last_inspection": "2025-06-10",
            "next_scheduled": "2025-08-25",
            "uptime": "96.5%",
            "workover_history": "2 times",
            "description": "Medium-production well with stable performance. Recently optimized with smaller choke size to extend plateau production.",
            "recent_operations": [
                "Choke size reduced to 28/64\" on 2025-05-10",
                "Production test conducted on 2025-04-15",
                "Downhole memory gauge installed on 2025-03-22",
                "Chemical treatment for scale prevention on 2025-02-18",
                "Surface equipment maintenance on 2025-01-05"
            ]
        },
        "Agartala-A#6": {
            "operator": "ONGC",
            "depth": "3400m",
            "reservoir": "Tipam Formation",
            "completion_date": "2019-07-09",
            "last_maintenance": "2025-02-28",
            "last_inspection": "2025-03-15",
            "next_scheduled": "2025-09-20",
            "uptime": "0%",
            "workover_history": "1 time",
            "description": "Currently shut-in due to mechanical issues. Workover planned for next quarter to replace downhole equipment and restore production.",
            "recent_operations": [
                "Well shut-in due to tubing leak on 2025-03-10",
                "Diagnostic survey completed on 2025-02-25",
                "Pressure build-up test conducted on 2025-02-10",
                "Surface control valve replaced on 2025-01-20",
                "Monthly production test on 2025-01-05"
            ]
        },
        
        # Konaban Field
        "Konaban-KO#1": {
            "operator": "ONGC",
            "depth": "3800m",
            "reservoir": "Barail Formation",
            "completion_date": "2018-05-30",
            "last_maintenance": "2025-03-22",
            "last_inspection": "2025-04-15",
            "next_scheduled": "2025-08-10",
            "uptime": "99.3%",
            "workover_history": "1 time",
            "description": "Flagship well of Konaban field with highest production rates. Equipped with artificial lift system for optimal recovery.",
            "recent_operations": [
                "Artificial lift system optimized on 2025-04-18",
                "Production logging test completed on 2025-03-28",
                "Choke size adjusted to 34/64\" on 2025-03-05",
                "Chemical injection system serviced on 2025-02-15",
                "Safety valve tested on 2025-01-20"
            ]
        },
        "Konaban-KO#2": {
            "operator": "ONGC",
            "depth": "3750m",
            "reservoir": "Barail Formation",
            "completion_date": "2019-02-14",
            "last_maintenance": "2025-04-05",
            "last_inspection": "2025-05-10",
            "next_scheduled": "2025-08-25",
            "uptime": "98.9%",
            "workover_history": "2 times",
            "description": "Reliable producer with consistent output. Recently underwent maintenance to replace surface valves and control systems.",
            "recent_operations": [
                "Surface valves replaced on 2025-04-05",
                "Control system upgraded on 2025-03-18",
                "Monthly pressure survey completed on 2025-03-05",
                "Chemical treatment for corrosion prevention on 2025-02-10",
                "Production test conducted on 2025-01-15"
            ]
        },
        "Konaban-KO#3": {
            "operator": "ONGC",
            "depth": "3900m",
            "reservoir": "Barail Formation",
            "completion_date": "2020-08-19",
            "last_maintenance": "2025-04-10",
            "last_inspection": "2025-05-15",
            "next_scheduled": "2025-09-15",
            "uptime": "97.6%",
            "workover_history": "1 time",
            "description": "Deep well with high initial pressure. Requires careful drawdown management to prevent water coning.",
            "recent_operations": [
                "Drawdown optimization completed on 2025-05-05",
                "Water cut monitoring sensors installed on 2025-04-18",
                "Production test conducted on 2025-03-25",
                "Choke size increased to 36/64\" on 2025-02-28",
                "Safety system inspection on 2025-01-15"
            ]
        },
        "Konaban-KO#4": {
            "operator": "ONGC",
            "depth": "3700m",
            "reservoir": "Barail Formation",
            "completion_date": "2021-03-25",
            "last_maintenance": "2024-12-10",
            "last_inspection": "2025-01-15",
            "next_scheduled": "2025-07-20",
            "uptime": "0%",
            "workover_history": "0 times",
            "description": "Shut-in due to sand ingress issues. Sand control measures being evaluated for implementation in next quarter.",
            "recent_operations": [
                "Sand control assessment started on 2025-02-10",
                "Well shut-in due to sand production on 2025-01-25",
                "Sand sampling completed on 2025-01-10",
                "Production logging test on 2024-12-20",
                "Choke size reduced to 24/64\" on 2024-12-05"
            ]
        },
        "Konaban-KO#5": {
            "operator": "ONGC",
            "depth": "3850m",
            "reservoir": "Barail Formation",
            "completion_date": "2022-01-11",
            "last_maintenance": "2025-05-20",
            "last_inspection": "2025-06-05",
            "next_scheduled": "2025-09-30",
            "uptime": "99.5%",
            "workover_history": "0 times",
            "description": "Newer well with artificial lift installed. Performing above expectations with excellent reservoir characteristics.",
            "recent_operations": [
                "Artificial lift system optimized on 2025-05-20",
                "Production test completed on 2025-05-05",
                "Downhole sensors calibrated on 2025-04-15",
                "Chemical treatment applied on 2025-03-28",
                "Safety valve tested on 2025-02-10"
            ]
        },
        
        # Manikyanagar Field
        "Manikyanagar-M#1": {
            "operator": "ONGC",
            "depth": "3600m",
            "reservoir": "Tipam Formation",
            "completion_date": "2019-08-15",
            "last_maintenance": "2025-04-10",
            "last_inspection": "2025-05-05",
            "next_scheduled": "2025-08-15",
            "uptime": "98.2%",
            "workover_history": "1 time",
            "description": "Reliable producer with consistent gas output. Requires regular monitoring of water cut.",
            "recent_operations": [
                "Water cut monitoring system upgraded on 2025-05-01",
                "Production test conducted on 2025-04-15",
                "Choke size adjusted to 30/64\" on 2025-03-20",
                "Chemical injection system serviced on 2025-02-25",
                "Safety inspection completed on 2025-01-10"
            ]
        },
        "Manikyanagar-M#2": {
            "operator": "ONGC",
            "depth": "3550m",
            "reservoir": "Tipam Formation",
            "completion_date": "2020-03-22",
            "last_maintenance": "2025-03-15",
            "last_inspection": "2025-04-10",
            "next_scheduled": "2025-07-25",
            "uptime": "97.8%",
            "workover_history": "0 times",
            "description": "Medium-production well with stable performance. Recently optimized for improved recovery.",
            "recent_operations": [
                "Production optimization completed on 2025-04-05",
                "Downhole pressure survey on 2025-03-18",
                "Chemical treatment for corrosion prevention on 2025-02-28",
                "Surface equipment maintenance on 2025-02-05",
                "Monthly production test on 2025-01-15"
            ]
        },
        "Manikyanagar-M#3": {
            "operator": "ONGC",
            "depth": "3650m",
            "reservoir": "Tipam Formation",
            "completion_date": "2021-11-10",
            "last_maintenance": "2024-12-20",
            "last_inspection": "2025-01-15",
            "next_scheduled": "2025-06-30",
            "uptime": "0%",
            "workover_history": "0 times",
            "description": "Currently shut-in due to mechanical issues. Diagnostic work scheduled for next month.",
            "recent_operations": [
                "Well shut-in due to control system failure on 2025-01-10",
                "Control system diagnostics started on 2025-01-05",
                "Production test conducted on 2024-12-20",
                "Safety valve tested on 2024-12-05",
                "Chemical treatment applied on 2024-11-20"
            ]
        },
        
        # Gojalia Field
        "Gojalia-G#1": {
            "operator": "ONGC",
            "depth": "3450m",
            "reservoir": "Barail Formation",
            "completion_date": "2020-07-18",
            "last_maintenance": "2025-04-25",
            "last_inspection": "2025-05-20",
            "next_scheduled": "2025-09-10",
            "uptime": "98.9%",
            "workover_history": "0 times",
            "description": "High-productivity well with excellent reservoir characteristics. Minimal maintenance required.",
            "recent_operations": [
                "Production optimization completed on 2025-05-10",
                "Downhole sensors calibrated on 2025-04-28",
                "Choke size adjusted to 32/64\" on 2025-04-05",
                "Chemical injection system serviced on 2025-03-15",
                "Safety inspection on 2025-02-20"
            ]
        },
        "Gojalia-G#2": {
            "operator": "ONGC",
            "depth": "3500m",
            "reservoir": "Barail Formation",
            "completion_date": "2021-02-14",
            "last_maintenance": "2025-03-28",
            "last_inspection": "2025-04-22",
            "next_scheduled": "2025-08-15",
            "uptime": "97.5%",
            "workover_history": "1 time",
            "description": "Medium-production well with stable output. Requires regular monitoring of pressure and temperature.",
            "recent_operations": [
                "Pressure and temperature monitoring upgraded on 2025-04-15",
                "Production test conducted on 2025-03-28",
                "Chemical treatment for scale prevention on 2025-03-05",
                "Surface control valve replaced on 2025-02-10",
                "Monthly maintenance on 2025-01-20"
            ]
        },
        "Gojalia-G#3": {
            "operator": "ONGC",
            "depth": "3400m",
            "reservoir": "Barail Formation",
            "completion_date": "2022-05-30",
            "last_maintenance": "2025-05-15",
            "last_inspection": "2025-06-05",
            "next_scheduled": "2025-09-20",
            "uptime": "99.2%",
            "workover_history": "0 times",
            "description": "Newest well in Gojalia field with advanced completion technology. Performing above expectations.",
            "recent_operations": [
                "Advanced monitoring system installed on 2025-05-25",
                "Production optimization completed on 2025-05-15",
                "Downhole gauge replaced on 2025-04-28",
                "Chemical treatment applied on 2025-04-10",
                "Safety system tested on 2025-03-20"
            ]
        },
        
        # Khubal Field
        "Khubal-KB#1": {
            "operator": "ONGC",
            "depth": "3200m",
            "reservoir": "Tipam Formation",
            "completion_date": "2018-11-20",
            "last_maintenance": "2025-03-10",
            "last_inspection": "2025-04-05",
            "next_scheduled": "2025-08-10",
            "uptime": "96.8%",
            "workover_history": "2 times",
            "description": "Mature well with declining production. Requires optimization for extended recovery.",
            "recent_operations": [
                "Production enhancement study started on 2025-04-15",
                "Downhole diagnostics completed on 2025-03-28",
                "Choke size reduced to 28/64\" on 2025-03-10",
                "Chemical treatment for corrosion prevention on 2025-02-18",
                "Safety inspection on 2025-01-25"
            ]
        },
        "Khubal-KB#2": {
            "operator": "ONGC",
            "depth": "3250m",
            "reservoir": "Tipam Formation",
            "completion_date": "2019-06-15",
            "last_maintenance": "2025-02-28",
            "last_inspection": "2025-03-25",
            "next_scheduled": "2025-07-20",
            "uptime": "97.3%",
            "workover_history": "1 time",
            "description": "Stable producer with consistent output. Minimal issues reported.",
            "recent_operations": [
                "Production test conducted on 2025-03-20",
                "Downhole pressure survey on 2025-03-05",
                "Surface equipment maintenance on 2025-02-15",
                "Chemical injection system serviced on 2025-01-28",
                "Safety valve tested on 2025-01-10"
            ]
        },
        "Khubal-KB#3": {
            "operator": "ONGC",
            "depth": "3300m",
            "reservoir": "Tipam Formation",
            "completion_date": "2020-09-05",
            "last_maintenance": "2024-12-15",
            "last_inspection": "2025-01-10",
            "next_scheduled": "2025-06-30",
            "uptime": "0%",
            "workover_history": "0 times",
            "description": "Shut-in due to mechanical failure. Workover planned for next quarter.",
            "recent_operations": [
                "Well shut-in due to tubing failure on 2025-01-15",
                "Diagnostic survey completed on 2025-01-05",
                "Production test conducted on 2024-12-20",
                "Chemical treatment applied on 2024-12-05",
                "Monthly maintenance on 2024-11-20"
            ]
        },
        "Khubal-KB#4": {
            "operator": "ONGC",
            "depth": "3150m",
            "reservoir": "Tipam Formation",
            "completion_date": "2021-04-18",
            "last_maintenance": "2025-04-01",
            "last_inspection": "2025-04-28",
            "next_scheduled": "2025-08-25",
            "uptime": "98.5%",
            "workover_history": "0 times",
            "description": "Newer well with advanced completion. Performing according to expectations.",
            "recent_operations": [
                "Production optimization completed on 2025-04-20",
                "Downhole sensors calibrated on 2025-04-10",
                "Choke size adjusted to 30/64\" on 2025-03-22",
                "Chemical injection system serviced on 2025-03-05",
                "Safety inspection on 2025-02-15"
            ]
        },
        "Khubal-BA#1": {
            "operator": "ONGC",
            "depth": "3350m",
            "reservoir": "Barail Formation",
            "completion_date": "2017-08-10",
            "last_maintenance": "2025-03-15",
            "last_inspection": "2025-04-10",
            "next_scheduled": "2025-08-05",
            "uptime": "96.2%",
            "workover_history": "3 times",
            "description": "Mature well with declining production. Scheduled for enhanced recovery techniques.",
            "recent_operations": [
                "Enhanced recovery study initiated on 2025-04-15",
                "Production test conducted on 2025-03-28",
                "Downhole diagnostics completed on 2025-03-15",
                "Chemical treatment for scale removal on 2025-02-20",
                "Surface equipment maintenance on 2025-01-25"
            ]
        },
        "Khubal-BA#2": {
            "operator": "ONGC",
            "depth": "3400m",
            "reservoir": "Barail Formation",
            "completion_date": "2018-05-22",
            "last_maintenance": "2025-04-05",
            "last_inspection": "2025-05-01",
            "next_scheduled": "2025-08-20",
            "uptime": "97.8%",
            "workover_history": "2 times",
            "description": "Stable producer with consistent output. Requires regular monitoring.",
            "recent_operations": [
                "Monitoring system upgraded on 2025-05-05",
                "Production test completed on 2025-04-15",
                "Choke size adjusted to 32/64\" on 2025-03-28",
                "Chemical injection system serviced on 2025-03-10",
                "Safety valve tested on 2025-02-15"
            ]
        },
        "Khubal-BA#3": {
            "operator": "ONGC",
            "depth": "3250m",
            "reservoir": "Barail Formation",
            "completion_date": "2019-02-15",
            "last_maintenance": "2023-10-20",
            "last_inspection": "2023-11-15",
            "next_scheduled": "N/A",
            "uptime": "0%",
            "workover_history": "1 time",
            "description": "Abandoned due to depleted reserves. Site secured and marked for future re-entry.",
            "recent_operations": [
                "Final abandonment completed on 2023-12-10",
                "Cement plug set at 3200m on 2023-11-28",
                "Wellhead removed and capped on 2023-11-10",
                "Environmental assessment on 2023-10-25",
                "Final production test on 2023-10-10"
            ]
        },
        "Khubal-BA#4": {
            "operator": "ONGC",
            "depth": "3300m",
            "reservoir": "Barail Formation",
            "completion_date": "2020-07-30",
            "last_maintenance": "2023-09-15",
            "last_inspection": "2023-10-10",
            "next_scheduled": "N/A",
            "uptime": "0%",
            "workover_history": "0 times",
            "description": "Abandoned due to poor reservoir performance. Site secured for future evaluation.",
            "recent_operations": [
                "Abandonment procedures completed on 2023-11-05",
                "Cement plug set at 3250m on 2023-10-20",
                "Wellhead secured on 2023-10-05",
                "Environmental clearance obtained on 2023-09-20",
                "Final diagnostics on 2023-09-05"
            ]
        },
        "Khubal-BA#5": {
            "operator": "ONGC",
            "depth": "3200m",
            "reservoir": "Barail Formation",
            "completion_date": "2021-03-10",
            "last_maintenance": "2023-08-01",
            "last_inspection": "2023-08-28",
            "next_scheduled": "N/A",
            "uptime": "0%",
            "workover_history": "0 times",
            "description": "Dry hole abandoned after completion. No commercial production achieved.",
            "recent_operations": [
                "Abandonment completed on 2023-09-15",
                "Cement plug set at 3150m on 2023-09-05",
                "Wellhead removed on 2023-08-20",
                "Site assessment on 2023-08-10",
                "Final evaluation on 2023-08-01"
            ]
        },
        "Khubal-BA#6": {
            "operator": "ONGC",
            "depth": "3350m",
            "reservoir": "Barail Formation",
            "completion_date": "2022-01-20",
            "last_maintenance": "2025-04-20",
            "last_inspection": "2025-05-15",
            "next_scheduled": "2025-09-10",
            "uptime": "98.3%",
            "workover_history": "0 times",
            "description": "Newer well with promising production rates. Requires monitoring of water cut.",
            "recent_operations": [
                "Water cut monitoring system installed on 2025-05-10",
                "Production test conducted on 2025-04-28",
                "Choke size adjusted to 28/64\" on 2025-04-10",
                "Chemical treatment applied on 2025-03-22",
                "Safety inspection on 2025-02-28"
            ]
        },
        "Khubal-BA#7": {
            "operator": "ONGC",
            "depth": "3400m",
            "reservoir": "Barail Formation",
            "completion_date": "2023-06-15",
            "last_maintenance": "2025-03-05",
            "last_inspection": "2025-03-30",
            "next_scheduled": "2025-07-25",
            "uptime": "0%",
            "workover_history": "0 times",
            "description": "Shut-in due to surface facility issues. Repairs scheduled for next month.",
            "recent_operations": [
                "Well shut-in due to pipeline issue on 2025-04-01",
                "Surface facility assessment on 2025-03-25",
                "Production test conducted on 2025-03-10",
                "Chemical injection system serviced on 2025-02-20",
                "Monthly maintenance on 2025-01-15"
            ]
        },
        
        # Sundalbari Field
        "Sundalbari-S#1": {
            "operator": "ONGC",
            "depth": "3500m",
            "reservoir": "Tipam Formation",
            "completion_date": "2019-09-10",
            "last_maintenance": "2025-04-15",
            "last_inspection": "2025-05-10",
            "next_scheduled": "2025-08-30",
            "uptime": "98.7%",
            "workover_history": "1 time",
            "description": "High-pressure gas well with excellent production characteristics. Minimal maintenance required.",
            "recent_operations": [
                "Pressure monitoring system upgraded on 2025-05-15",
                "Production test completed on 2025-04-28",
                "Choke size adjusted to 34/64\" on 2025-04-10",
                "Chemical treatment applied on 2025-03-25",
                "Safety valve tested on 2025-02-28"
            ]
        },
        "Sundalbari-S#2": {
            "operator": "ONGC",
            "depth": "3450m",
            "reservoir": "Tipam Formation",
            "completion_date": "2020-04-18",
            "last_maintenance": "2025-03-20",
            "last_inspection": "2025-04-15",
            "next_scheduled": "2025-08-10",
            "uptime": "97.5%",
            "workover_history": "0 times",
            "description": "Medium-production well with stable output. Requires regular monitoring.",
            "recent_operations": [
                "Monitoring system calibrated on 2025-04-20",
                "Production test conducted on 2025-04-05",
                "Downhole diagnostics on 2025-03-20",
                "Chemical injection system serviced on 2025-03-05",
                "Safety inspection on 2025-02-10"
            ]
        },
        "Sundalbari-S#3": {
            "operator": "ONGC",
            "depth": "3550m",
            "reservoir": "Tipam Formation",
            "completion_date": "2021-08-05",
            "last_maintenance": "2023-11-15",
            "last_inspection": "2023-12-10",
            "next_scheduled": "N/A",
            "uptime": "0%",
            "workover_history": "0 times",
            "description": "Abandoned due to water breakthrough issues. Site secured for future evaluation.",
            "recent_operations": [
                "Abandonment completed on 2024-01-10",
                "Cement plug set at 3500m on 2023-12-20",
                "Wellhead secured on 2023-12-05",
                "Environmental assessment on 2023-11-25",
                "Final diagnostics on 2023-11-10"
            ]
        },
        "Sundalbari-S#4": {
            "operator": "ONGC",
            "depth": "3400m",
            "reservoir": "Tipam Formation",
            "completion_date": "2022-03-22",
            "last_maintenance": "2025-01-10",
            "last_inspection": "2025-02-05",
            "next_scheduled": "2025-06-15",
            "uptime": "0%",
            "workover_history": "0 times",
            "description": "Shut-in due to mechanical issues. Diagnostic work scheduled for next week.",
            "recent_operations": [
                "Well shut-in due to pump failure on 2025-02-15",
                "Diagnostic assessment started on 2025-02-10",
                "Production test conducted on 2025-01-28",
                "Chemical treatment applied on 2025-01-15",
                "Monthly maintenance on 2024-12-20"
            ]
        },
        "Sundalbari-S#5": {
            "operator": "ONGC",
            "depth": "3500m",
            "reservoir": "Tipam Formation",
            "completion_date": "2023-01-15",
            "last_maintenance": "2025-05-01",
            "last_inspection": "2025-05-28",
            "next_scheduled": "2025-09-15",
            "uptime": "99.0%",
            "workover_history": "0 times",
            "description": "Newest well in Sundalbari field with advanced completion technology. Performing above expectations.",
            "recent_operations": [
                "Advanced monitoring system installed on 2025-05-20",
                "Production optimization completed on 2025-05-10",
                "Downhole sensors calibrated on 2025-04-25",
                "Chemical treatment applied on 2025-04-10",
                "Safety system tested on 2025-03-20"
            ]
        },
        
        # Tichna Field
        "Tichna-T#1": {
            "operator": "ONGC",
            "depth": "3300m",
            "reservoir": "Barail Formation",
            "completion_date": "2020-06-12",
            "last_maintenance": "2025-04-10",
            "last_inspection": "2025-05-05",
            "next_scheduled": "2025-08-20",
            "uptime": "97.2%",
            "workover_history": "1 time",
            "description": "Stable producer with consistent output. Requires monitoring of pressure decline.",
            "recent_operations": [
                "Pressure decline analysis completed on 2025-05-10",
                "Production test conducted on 2025-04-22",
                "Choke size adjusted to 30/64\" on 2025-04-05",
                "Chemical injection system serviced on 2025-03-15",
                "Safety inspection on 2025-02-20"
            ]
        },
        "Tichna-T#2": {
            "operator": "ONGC",
            "depth": "3350m",
            "reservoir": "Barail Formation",
            "completion_date": "2021-03-18",
            "last_maintenance": "2025-01-15",
            "last_inspection": "2025-02-10",
            "next_scheduled": "2025-06-30",
            "uptime": "0%",
            "workover_history": "0 times",
            "description": "Shut-in due to surface facility constraints. Awaiting pipeline connection.",
            "recent_operations": [
                "Well shut-in pending pipeline connection on 2025-02-20",
                "Surface facilities completed on 2025-02-10",
                "Production test conducted on 2025-01-28",
                "Chemical treatment applied on 2025-01-15",
                "Safety inspection on 2024-12-20"
            ]
        },
        "Tichna-T#3": {
            "operator": "ONGC",
            "depth": "3400m",
            "reservoir": "Barail Formation",
            "completion_date": "2022-08-25",
            "last_maintenance": "2025-05-15",
            "last_inspection": "2025-06-05",
            "next_scheduled": "2025-09-25",
            "uptime": "98.8%",
            "workover_history": "0 times",
            "description": "New well with promising initial production. Requires monitoring of decline curve.",
            "recent_operations": [
                "Decline curve analysis started on 2025-06-01",
                "Production test completed on 2025-05-20",
                "Downhole sensors calibrated on 2025-05-05",
                "Chemical treatment applied on 2025-04-18",
                "Safety system tested on 2025-03-28"
            ]
        },
        
        # Kunjaban Field
        "Kunjaban-KJ#1": {
            "operator": "ONGC",
            "depth": "3250m",
            "reservoir": "Tipam Formation",
            "completion_date": "2021-05-20",
            "last_maintenance": "2025-04-05",
            "last_inspection": "2025-04-30",
            "next_scheduled": "2025-08-15",
            "uptime": "97.5%",
            "workover_history": "0 times",
            "description": "Medium-production well with stable output. Minimal maintenance required.",
            "recent_operations": [
                "Production test conducted on 2025-04-20",
                "Downhole pressure survey on 2025-04-10",
                "Choke size adjusted to 28/64\" on 2025-03-25",
                "Chemical injection system serviced on 2025-03-10",
                "Safety inspection on 2025-02-15"
            ]
        },
        "Kunjaban-KJ#2": {
            "operator": "ONGC",
            "depth": "3300m",
            "reservoir": "Tipam Formation",
            "completion_date": "2022-02-15",
            "last_maintenance": "2025-03-18",
            "last_inspection": "2025-04-12",
            "next_scheduled": "2025-08-10",
            "uptime": "98.2%",
            "workover_history": "0 times",
            "description": "Reliable producer with consistent gas output. Requires monitoring of water production.",
            "recent_operations": [
                "Water production monitoring upgraded on 2025-04-15",
                "Production test completed on 2025-04-01",
                "Downhole diagnostics on 2025-03-18",
                "Chemical treatment for corrosion prevention on 2025-03-05",
                "Safety valve tested on 2025-02-10"
            ]
        },
        "Kunjaban-KJ#3": {
            "operator": "ONGC",
            "depth": "3350m",
            "reservoir": "Tipam Formation",
            "completion_date": "2023-04-10",
            "last_maintenance": "2025-01-20",
            "last_inspection": "2025-02-15",
            "next_scheduled": "2025-06-25",
            "uptime": "0%",
            "workover_history": "0 times",
            "description": "Shut-in due to reservoir performance issues. Evaluation in progress.",
            "recent_operations": [
                "Well shut-in for reservoir evaluation on 2025-02-25",
                "Reservoir assessment started on 2025-02-15",
                "Production test conducted on 2025-01-30",
                "Chemical treatment applied on 2025-01-20",
                "Monthly maintenance on 2024-12-15"
            ]
        },
        "Kunjaban-KJ#4": {
            "operator": "ONGC",
            "depth": "3400m",
            "reservoir": "Tipam Formation",
            "completion_date": "2023-11-05",
            "last_maintenance": "2025-05-10",
            "last_inspection": "2025-06-01",
            "next_scheduled": "2025-09-30",
            "uptime": "99.3%",
            "workover_history": "0 times",
            "description": "Newest well in Kunjaban field with advanced completion. Excellent initial performance.",
            "recent_operations": [
                "Initial production optimization completed on 2025-05-25",
                "Downhole monitoring system installed on 2025-05-15",
                "Production test conducted on 2025-05-05",
                "Chemical treatment applied on 2025-04-20",
                "Safety system tested on 2025-03-28"
            ]
        }
    }

    CSV_DATA = """Field,Well,FTHP,Qg,Qw,Qc, status
Agartala,A#1,33,36000,5.29,0.147,Flowing
Agartala,A#2,37,56321,7.95,0.197,Flowing
Agartala,A#3,116,81987,0.8,0.039,Flowing
Agartala,A#4,,,,,Dry/Abandoned
Agartala,A#5,56,27512,3.12,0.031,Flowing
Agartala,A#6,38,,,,Sick
Konaban,KO#1,109,126412,1.3,0.013,Flowing
Konaban,KO#2,107,97751,0.1,0.001,Flowing
Konaban,KO#3,38,29750,1,0.196,Flowing
Konaban,KO#4,51,,,,Sick
Konaban,KO#5,25,25846,0.1,0.001,Flowing
Manikyanagar,M#1,60,39017,2.4,0.071,Flowing
Manikyanagar,M#2,43,65321,3.12,0.215,Flowing
Manikyanagar,M#3,31,,,,Sick
Gojalia,G#1,62,88124,2,0.079,Flowing
Gojalia,G#2,71,63020,1.86,0.092,Flowing
Gojalia,G#3,52,35760,0.2,0.039,Flowing
Khubal,KB#1,6,927,0.25,0.001,Flowing
Khubal,KB#2,26,23184,2,0.02,
Khubal,KB#3,,,,,Sick
Khubal,KB#4,,,,,
Khubal,BA#1,29,17560,1.8,0.009,
Khubal,BA#2,50,56028,5.5,0.05,
Khubal,BA#3,,,,,Dry/Abandoned
Khubal,BA#4,,,,,Dry/Abandoned
Khubal,BA#5,,,,,Dry/Abandoned
Khubal,BA#6,26,20592,0.3,0.006,
Khubal,BA#7,35,,,,Sick
Sundalbari,S#1,0,86254,1.6,0,
Sundalbari,S#2,82,53245,1.81,0.082,
Sundalbari,S#3,,,,,Dry/Abandoned
Sundalbari,S#4,,,,,Sick
Sundalbari,S#5,52,22452,1.8,0.016,
Tichna,T#1,40,2012,1.02,0.042,
Tichna,T#2,46,,,,Sick
Tichna,T#3,25,34311,1.3,0.102,
Kunjaban,KJ#1,21,7920,0.2,0.002,
Kunjaban,KJ#2,44,58615,0.8,0.055,
Kunjaban,KJ#3,35,,,,Sick
Kunjaban,KJ#4,23,3216,0,0,"""

    if Well.query.first() is None: # Only populate if the wells table is empty
        reader = csv.DictReader(CSV_DATA.splitlines())
        for row in reader:
            field_name = row['Field'].strip()
            well_id = row['Well'].strip()
            well_key = f"{field_name}-{well_id}"
            
            details = WELL_DETAILS.get(well_key, {})

            # Convert 'N/A' or empty strings to None, and then to appropriate types
            fthp = float(row['FTHP']) if row['FTHP'] and row['FTHP'] != 'N/A' else None
            qg = float(row['Qg']) if row['Qg'] and row['Qg'] != 'N/A' else None
            qw = float(row['Qw']) if row['Qw'] and row['Qw'] != 'N/A' else None
            qc = float(row['Qc']) if row['Qc'] and row['Qc'] != 'N/A' else None
            
            # Clean up the status field
            status = row[' status'].strip() if row[' status'].strip() else 'Unknown'

            # Convert date strings to datetime.date objects
            completion_date = datetime.strptime(details.get('completion_date'), '%Y-%m-%d').date() if details.get('completion_date') else None
            last_maintenance = datetime.strptime(details.get('last_maintenance'), '%Y-%m-%d').date() if details.get('last_maintenance') else None
            last_inspection = datetime.strptime(details.get('last_inspection'), '%Y-%m-%d').date() if details.get('last_inspection') else None
            
            # Handle 'N/A' for next_scheduled as it's a string column
            next_scheduled = details.get('next_scheduled') if details.get('next_scheduled') != 'N/A' else None


            new_well = Well(
                field_name=field_name,
                well_id=well_id,
                fthp=fthp,
                qg=qg,
                qw=qw,
                qc=qc,
                status=status,
                operator=details.get('operator'),
                depth=details.get('depth'),
                reservoir=details.get('reservoir'),
                completion_date=completion_date,
                last_maintenance=last_maintenance,
                last_inspection=last_inspection,
                next_scheduled=next_scheduled,
                uptime=details.get('uptime'),
                workover_history=details.get('workover_history'),
                description=details.get('description'),
                recent_operations=details.get('recent_operations', []) # Use the setter property
            )
            db.session.add(new_well)
        db.session.commit()
        print("Initial well data populated into the database.")


# Call the function to populate wells when the app starts, but only if the table is empty
with app.app_context():
    populate_wells_from_initial_data()


# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Login routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()

        # Use check_password_hash for secure password comparison
        if user and check_password_hash(user.password, password):
            session['user_email'] = user.email
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid credentials")
    
    return render_template('login.html')

@app.route('/signup', methods=['POST'])
def signup():
    name = request.form['name']
    email = request.form['email']
    department = request.form['department']
    password = request.form['password']
    confirm = request.form['confirm']
    
    if not email.endswith('@ongc.co.in'):
        return render_template('login.html', signup_error="Please use your ONGC company email")
    
    if password != confirm:
        return render_template('login.html', signup_error="Passwords do not match")
    
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return render_template('login.html', signup_error="Email already registered")
    
    # Hash the password before storing
    hashed_password = generate_password_hash(password)
    new_user = User(name=name, email=email, password=hashed_password, department=department, role='user')

    db.session.add(new_user)
    db.session.commit()
    
    session['user_email'] = new_user.email
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('user_email', None)
    return redirect(url_for('home'))

# Home page
@app.route('/')
def home():
    return render_template('home.html')

# Function to get well data from the database
def get_well_data_from_db():
    wells_from_db = Well.query.all()
    
    well_data = []
    stats = {
        'total_wells': 0,
        'active': 0,
        'sick': 0,
        'dry': 0,
        'flowing': 0,
        'unknown': 0
    }

    for well_obj in wells_from_db:
        # Construct the well dictionary similar to your original structure
        well = {
            'field': well_obj.field_name,
            'id': well_obj.well_id,
            'fthp': well_obj.fthp if well_obj.fthp is not None else 'N/A',
            'qg': well_obj.qg if well_obj.qg is not None else 'N/A',
            'qw': well_obj.qw if well_obj.qw is not None else 'N/A',
            'qc': well_obj.qc if well_obj.qc is not None else 'N/A',
            'status': well_obj.status,
            'key': f"{well_obj.field_name}-{well_obj.well_id}",
            'details': {
                'operator': well_obj.operator,
                'depth': well_obj.depth,
                'reservoir': well_obj.reservoir,
                'completion_date': well_obj.completion_date.strftime('%Y-%m-%d') if well_obj.completion_date else 'N/A',
                'last_maintenance': well_obj.last_maintenance.strftime('%Y-%m-%d') if well_obj.last_maintenance else 'N/A',
                'last_inspection': well_obj.last_inspection.strftime('%Y-%m-%d') if well_obj.last_inspection else 'N/A',
                'next_scheduled': well_obj.next_scheduled if well_obj.next_scheduled else 'N/A',
                'uptime': well_obj.uptime,
                'workover_history': well_obj.workover_history,
                'description': well_obj.description,
                'recent_operations': well_obj.recent_operations # This uses the @property
            }
        }
        well_data.append(well)

        # Update statistics
        stats['total_wells'] += 1
        if 'flow' in well_obj.status.lower():
            stats['flowing'] += 1
            stats['active'] += 1
        elif 'sick' in well_obj.status.lower():
            stats['sick'] += 1
        elif 'dry' in well_obj.status.lower() or 'abandoned' in well_obj.status.lower():
            stats['dry'] += 1
        else: # For 'Unknown' or any other status not explicitly handled
            stats['unknown'] += 1
    
    return well_data, stats


# Route for the dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    well_data, stats = get_well_data_from_db()
    # Fetch user details for the header
    user_email = session.get('user_email')
    logged_in_user = User.query.filter_by(email=user_email).first()
    return render_template('index.html', wells=well_data, stats=stats, active_page='dashboard', session_user=logged_in_user.name if logged_in_user else 'Guest')

# Route for well details
@app.route('/well/<well_key>')
@login_required
def well_details(well_key):
    parts = well_key.split('-')
    if len(parts) != 2:
        return "Invalid well key format", 400
    field_name, well_id = parts[0], parts[1]

    well_obj = Well.query.filter_by(field_name=field_name, well_id=well_id).first()
    
    if not well_obj:
        return "Well not found", 404

    well = {
        'field': well_obj.field_name,
        'id': well_obj.well_id,
        'fthp': well_obj.fthp if well_obj.fthp is not None else 'N/A',
        'qg': well_obj.qg if well_obj.qg is not None else 'N/A',
        'qw': well_obj.qw if well_obj.qw is not None else 'N/A',
        'qc': well_obj.qc if well_obj.qc is not None else 'N/A',
        'status': well_obj.status,
        'key': f"{well_obj.field_name}-{well_obj.well_id}",
        'details': {
            'operator': well_obj.operator,
            'depth': well_obj.depth,
            'reservoir': well_obj.reservoir,
            'completion_date': well_obj.completion_date.strftime('%Y-%m-%d') if well_obj.completion_date else 'N/A',
            'last_maintenance': well_obj.last_maintenance.strftime('%Y-%m-%d') if well_obj.last_maintenance else 'N/A',
            'last_inspection': well_obj.last_inspection.strftime('%Y-%m-%d') if well_obj.last_inspection else 'N/A',
            'next_scheduled': well_obj.next_scheduled if well_obj.next_scheduled else 'N/A',
            'uptime': well_obj.uptime,
            'workover_history': well_obj.workover_history,
            'description': well_obj.description,
            'recent_operations': well_obj.recent_operations
        }
    }
    
    user_email = session.get('user_email')
    logged_in_user = User.query.filter_by(email=user_email).first()
    return render_template('well_details.html', well=well, active_page='dashboard', session_user=logged_in_user.name if logged_in_user else 'Guest')

# Route for settings page
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    user_email = session.get('user_email')
    logged_in_user = User.query.filter_by(email=user_email).first()

    if request.method == 'POST':
        # Handle profile update
        fullname = request.form['fullname']
        department = request.form['department']
        
        # Update user object and commit to DB
        if logged_in_user:
            logged_in_user.name = fullname
            logged_in_user.department = department
            db.session.commit()
            # Optionally, update session with new name if needed for immediate display elsewhere
            # session['user_name'] = fullname 
            return jsonify(success=True, message="Profile updated successfully!")
        return jsonify(success=False, message="User not found."), 404

    # GET request: Render the settings page with current user data
    return render_template('settings.html', 
                           active_page='settings', 
                           session_user=logged_in_user.name if logged_in_user else 'Guest',
                           user_data={
                               'email': logged_in_user.email,
                               'fullname': logged_in_user.name,
                               'department': logged_in_user.department
                           } if logged_in_user else {}
                        )

# API endpoint for updating profile (can be called by JS)
@app.route('/api/update_profile', methods=['POST'])
@login_required
def api_update_profile():
    user_email = session.get('user_email')
    logged_in_user = User.query.filter_by(email=user_email).first()

    if not logged_in_user:
        return jsonify(success=False, message="User not logged in or found."), 401

    data = request.get_json()
    fullname = data.get('fullname')
    department = data.get('department')
    
    if not fullname or not department:
        return jsonify(success=False, message="Full Name and Department are required."), 400

    try:
        logged_in_user.name = fullname
        logged_in_user.department = department
        db.session.commit()
        return jsonify(success=True, message="Profile updated successfully!")
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"Error updating profile: {str(e)}"), 500


# Route for analytics page
@app.route('/analytics')
@login_required
def analytics():
    user_email = session.get('user_email')
    logged_in_user = User.query.filter_by(email=user_email).first()
    return render_template('analytics.html', active_page='analytics', session_user=logged_in_user.name if logged_in_user else 'Guest')

@app.route('/map_view')
@login_required
def map_view():
    user_email = session.get('user_email')
    logged_in_user = User.query.filter_by(email=user_email).first()
    return render_template('map_view.html', session_user=logged_in_user.name if logged_in_user else 'Guest')

# API endpoint for well data
@app.route('/api/wells')
@login_required
def api_wells():
    well_data, _ = get_well_data_from_db()
    return jsonify(well_data)

# API endpoint for statistics
@app.route('/api/stats')
@login_required
def api_stats():
    _, stats = get_well_data_from_db()
    return jsonify(stats)

# API endpoints for analytics data (keep as is)

@app.route('/api/analytics/trend')
def get_trend_data():
    """
    Provides simulated production trend data for a given period.
    Fetches historical production data from a simulated source.
    """
    period_days = int(request.args.get('period', 180)) # Default to last 180 days
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_days)
    
    dates = []
    actual_production_data = []
    
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date.strftime('%Y-%m-%d'))
        # Simulate actual production data (replace with actual database query)
        actual_production_data.append(random.uniform(500, 1200)) # m³/d
        current_date += timedelta(days=1)

    response_data = {
        "labels": dates,
        "datasets": [
            {
                "label": "Actual Production",
                "data": actual_production_data
            }
        ]
    }
    return jsonify(response_data)

@app.route('/api/analytics/efficiency')
def get_efficiency_data():
    """
    Provides simulated field efficiency metrics data for a radar chart.
    """
    # Example dummy data for efficiency metrics (replace with real data)
    return jsonify({
        "labels": ["Uptime (%)", "Throughput (m³/d)", "Maintenance Cost (INR)", "Energy Consumption (kWh)", "Safety Incidents"],
        "datasets": [{
            "label": "Field A Efficiency",
            "data": [random.uniform(70, 95), random.uniform(800, 1500), random.uniform(10000, 50000), random.uniform(500, 1000), random.randint(0, 5)] 
        }]
    })

@app.route('/api/analytics/performance')
def get_performance_data():
    """
    Provides simulated well performance comparison data for a bar chart.
    """
    # Example dummy data for well performance comparison (replace with real data)
    wells = ["Well A-1", "Well B-2", "Well C-3", "Well D-4", "Well E-5"]
    oil_production = [random.uniform(100, 500) for _ in wells] # BPD
    gas_production = [random.uniform(5000, 20000) for _ in wells] # m³/d

    return jsonify({
        "labels": wells,
        "datasets": [{
            "label": "Oil Production (BPD)",
            "data": oil_production,
            "backgroundColor": "rgba(161, 13, 13, 0.8)"
        },
        {
            "label": "Gas Production (m³/d)",
            "data": gas_production,
            "backgroundColor": "rgba(255, 111, 0, 0.8)"
        }]
    })

@app.route('/api/analytics/anomaly')
def get_anomaly_data():
    """
    Provides simulated anomaly detection data for a scatter chart.
    Simulates normal operating points and a few anomalies based on FTHP and Gas Production.
    """
    # Simulate normal operating points
    normal_points = []
    for i in range(50):
        fthp = random.uniform(80, 150)
        gas_prod = random.uniform(1000, 2500)
        normal_points.append({'x': fthp, 'y': gas_prod, 'well_id': f'NW-{i+1}'})

    # Simulate anomaly points (outliers)
    anomaly_points = [
        {'x': random.uniform(20, 70), 'y': random.uniform(2000, 3000), 'well_id': 'AN-001'}, # High gas, low FTHP
        {'x': random.uniform(160, 200), 'y': random.uniform(500, 1000), 'well_id': 'AN-002'}, # Low gas, high FTHP
        {'x': random.uniform(100, 120), 'y': random.uniform(100, 400), 'well_id': 'AN-003'}, # Very low gas
        {'x': random.uniform(100, 120), 'y': random.uniform(3000, 3500), 'well_id': 'AN-004'}  # Very high gas
    ]

    return jsonify({
        "labels": [], # Not directly used for scatter plot labels
        "datasets": [
            {
                "label": "Normal Wells",
                "data": normal_points,
                "backgroundColor": "rgba(76, 175, 80, 0.8)", # Green
                "borderColor": "rgb(76, 175, 80)",
                "pointRadius": 4
            },
            {
                "label": "Anomaly",
                "data": anomaly_points,
                "backgroundColor": "rgba(244, 67, 54, 0.8)", # Red
                "borderColor": "rgb(244, 67, 54)",
                "pointRadius": 6
            }
        ]
    })

@app.route('/api/analytics/forecast')
def get_forecast_data():
    """
    Provides simulated production forecast data.
    Includes historical actuals and future forecasted values.
    """
    period_days = int(request.args.get('period', 180)) # Historical period for forecast
    
    end_date_historical = datetime.now()
    start_date_historical = end_date_historical - timedelta(days=period_days)
    
    # Forecast 30 days into the future
    forecast_days = 30 
    end_date_forecast = end_date_historical + timedelta(days=forecast_days)

    all_dates = []
    actual_production = []
    forecast_production = []

    # Generate historical actual data
    current_date = start_date_historical
    while current_date <= end_date_historical:
        all_dates.append(current_date.strftime('%Y-%m-%d'))
        # Simulate historical actual production
        actual_production.append(random.uniform(500, 1200)) # m³/d
        forecast_production.append(None) # No forecast for historical actuals
        current_date += timedelta(days=1)

    # Generate forecast dates and data
    current_date = end_date_historical + timedelta(days=1)
    while current_date <= end_date_forecast:
        all_dates.append(current_date.strftime('%Y-%m-%d'))
        actual_production.append(None) # No actuals for future forecast
        # Simulate forecast data (replace with actual forecast model output)
        # Simple projection from the last actual point
        last_actual_value = actual_production[-1] if actual_production else random.uniform(800, 1000)
        forecast_val = last_actual_value + random.uniform(-50, 50)
        forecast_production.append(max(0, forecast_val)) # Ensure non-negative production
        current_date += timedelta(days=1)

    response_data = {
        "labels": all_dates,
        "datasets": [
            {
                "label": "Actual Production",
                "data": actual_production
            },
            {
                "label": "Forecast",
                "data": forecast_production
            }
        ]
    }
    return jsonify(response_data)


if __name__ == '__main__':
    app.run(debug=True)
