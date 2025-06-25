import os
import csv
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from functools import wraps
import random
from datetime import datetime, timedelta
from flask import send_from_directory

app = Flask(__name__, static_folder='static')
app.secret_key = 'ongc_secret_key_2025'

# User database
USERS = {
    "admin@ongc.co.in": {
        "name": "Admin User",
        "password": "securepassword",
        "department": "IT",
        "role": "admin"
    },
    "engineer@ongc.co.in": {
        "name": "Field Engineer",
        "password": "ongc1234",
        "department": "Operations",
        "role": "user"
    }
}

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Generate random dates for operations
def generate_random_dates(count=5):
    base_date = datetime.now()
    return [f"{base_date - timedelta(days=random.randint(30, 180)):%Y-%m-%d}" for _ in range(count)]

# Well details dictionary with all wells
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


# Function to read and process CSV data
def get_well_data():
    well_data = []
    stats = {
        'total_wells': 0,
        'active': 0,
        'sick': 0,
        'dry': 0,
        'flowing': 0,
        'unknown': 0
    }
    
    # Read the CSV data
    csv_data = """Field,Well,FTHP,Qg,Qw,Qc, status
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
    
    # Parse the CSV data
    reader = csv.DictReader(csv_data.splitlines())
    for row in reader:
        # Clean up the status field
        status = row[' status'].strip() if row[' status'].strip() else 'Unknown'
        well_key = f"{row['Field']}-{row['Well']}"
        details = WELL_DETAILS.get(well_key, {})
        
        # Create a well dictionary
        well = {
            'field': row['Field'],
            'id': row['Well'],
            'fthp': row['FTHP'] if row['FTHP'] else 'N/A',
            'qg': row['Qg'] if row['Qg'] else 'N/A',
            'qw': row['Qw'] if row['Qw'] else 'N/A',
            'qc': row['Qc'] if row['Qc'] else 'N/A',
            'status': status,
            'key': well_key,
            'details': details
        }
        
        # Add to the list
        well_data.append(well)
        
        # Update statistics
        stats['total_wells'] += 1
        if 'flow' in status.lower():
            stats['flowing'] += 1
            stats['active'] += 1
        elif 'sick' in status.lower():
            stats['sick'] += 1
        elif 'dry' in status.lower() or 'abandoned' in status.lower():
            stats['dry'] += 1
        elif 'unknown' in status.lower():
            stats['unknown'] += 1
    
    return well_data,stats

# Login routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = USERS.get(email)
        if user and user['password'] == password:
            session['user'] = email
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
    
    if email in USERS:
        return render_template('login.html', signup_error="Email already registered")
    
    # Add to database
    USERS[email] = {
        "name": name,
        "password": password,
        "department": department,
        "role": "user"
    }
    session['user'] = email
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

# Home page
@app.route('/')
def home():
    return render_template('home.html')


# Route for the dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    well_data, stats = get_well_data()
    return render_template('index.html', wells=well_data, stats=stats, active_page='dashboard')

# Route for well details
@app.route('/well/<well_key>')
@login_required
def well_details(well_key):
    well_data, _ = get_well_data()
    well = next((w for w in well_data if w['key'] == well_key), None)
    
    if not well:
        return "Well not found", 404
        
    return render_template('well_details.html', well=well, active_page='dashboard')

# Route for settings page
@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html', active_page='settings')

# Route for analytics page
@app.route('/analytics')
@login_required
def analytics():
    return render_template('analytics.html', active_page='analytics')

@app.route('/map_view')
@login_required
def map_view():
    return render_template('map_view.html')

# API endpoint for well data
@app.route('/api/wells')
@login_required
def api_wells():
    well_data, _ = get_well_data()
    return jsonify(well_data)

# API endpoint for statistics
@app.route('/api/stats')
@login_required
def api_stats():
    _, stats = get_well_data()
    return jsonify(stats)

# API endpoints for analytics data
@app.route('/api/analytics/trend')
def trend_data():
    return jsonify({
        'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'datasets': [
            {
                'label': 'Gas Production (m³/d)',
                'data': [1200000, 1250000, 1180000, 1300000, 1350000, 1400000],
            },
            {
                'label': 'Water Production (bbl/d)',
                'data': [1200, 1250, 1300, 1180, 1100, 1050],
            }
        ]
    })

@app.route('/api/analytics/efficiency')
def efficiency_data():
    return jsonify({
        'labels': ['Production', 'Uptime', 'Safety', 'Cost', 'Efficiency', 'Maintenance'],
        'datasets': [
            {
                'label': 'Agartala',
                'data': [85, 78, 92, 88, 80, 75],
            },
            {
                'label': 'Konaban',
                'data': [92, 85, 88, 80, 85, 90],
            },
            {
                'label': 'Manikyanagar',
                'data': [78, 90, 85, 82, 88, 80],
            }
        ]
    })

@app.route('/api/analytics/performance')
def performance_data():
    return jsonify({
        'labels': ['A#1', 'A#2', 'KO#1', 'KO#2', 'M#1', 'M#2', 'G#1', 'G#2'],
        'datasets': [
            {
                'label': 'Actual Production',
                'data': [36000, 56321, 126412, 97751, 39017, 65321, 88124, 63020],
            },
            {
                'label': 'Target Production',
                'data': [35000, 55000, 125000, 95000, 40000, 65000, 90000, 62000],
            }
        ]
    })

@app.route('/api/analytics/anomaly')
def anomaly_data():
    return jsonify({
        'datasets': [
            {
                'label': 'Normal',
                'data': [
                    {'x': 30, 'y': 35000}, {'x': 35, 'y': 40000}, {'x': 40, 'y': 45000},
                    {'x': 45, 'y': 50000}, {'x': 50, 'y': 55000}, {'x': 55, 'y': 60000},
                    {'x': 60, 'y': 65000}, {'x': 65, 'y': 70000}, {'x': 70, 'y': 75000}
                ]
            },
            {
                'label': 'Anomaly',
                'data': [
                    {'x': 25, 'y': 80000}, {'x': 75, 'y': 30000}, {'x': 40, 'y': 20000},
                    {'x': 65, 'y': 85000}, {'x': 30, 'y': 90000}
                ]
            }
        ]
    })

@app.route('/api/analytics/forecast')
def forecast_data():
    return jsonify({
        'labels': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        'datasets': [
            {
                'label': 'Actual Production',
                'data': [1200000, 1250000, 1180000, 1300000, 1350000, 1400000, None, None, None, None, None, None]
            },
            {
                'label': 'Forecast',
                'data': [None, None, None, None, None, 1400000, 1420000, 1450000, 1470000, 1490000, 1520000, 1550000]
            }
        ]
    })

if __name__ == '__main__':
    app.run(debug=True)