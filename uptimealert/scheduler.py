from init_celery import celery
from app import db
from app import mail
from models import Monitor, User
from datetime import datetime, timedelta
from flask_mail import Message
from contextlib import closing
import requests
import subprocess
import socket


def check_socket(host, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        if sock.connect_ex((host, port)) == 0:
            return True
        else:
            return False


def send_email(monitor, email, username):
    timestamp = monitor.last_checked_at.strftime("%d-%m-%Y %H:%M:%S")

    state = "DOWN"
    if monitor.status:
        state = "UP"

    msg = Message(f'Alert! {monitor.name} is {state}', recipients=[email])
    msg.body = (f"Hi, {username}. Your monitor {monitor.name}\n"
                f"is {state} since our last check at {timestamp}")
    mail.send(msg)


@celery.task
def ping_servers():
    print(f"SCHEDULER IS RUNNING")

    monitors = db.session.query(Monitor, User.email, User.username).join(User, Monitor.user_id == User.id).all()

    for monitor, email, username in monitors:
        now = datetime.now()
        next_minute = now + timedelta(minutes=1)
        timestamp = now.strftime("%d-%m-%Y %H:%M:%S")
        current_status = None

        if monitor.status is not None:
            current_status = monitor.status

        if monitor.last_checked_at is None or next_minute > monitor.last_checked_at + timedelta(minutes=monitor.interval):
            monitor.last_checked_at = now

            if monitor.type == "ping":
                monitor.status = subprocess.call(['ping', '-c', '1', monitor.hostname]) == 0
                print(f"PING | {timestamp} | {monitor.status}")

            if monitor.type == "port":
                monitor.status = check_socket(monitor.hostname, monitor.port)
                # monitor.status = "open" in str(
                    # subprocess.run(['nmap', '-p', str(monitor.port), monitor.hostname], capture_output=True).stdout)
                print(f"PORT | {timestamp} | {monitor.status}")

            if monitor.type == "http":
#                try:
                response = requests.get(f"{monitor.hostname}", timeout=10)
                if response.ok or response.is_redirect:
                    monitor.status = True
                else:
                    monitor.status = False
#                except requests.RequestException:
#                    monitor.status = False
                print(f"HTTP | {timestamp} | {monitor.status} | {response.status_code}")

            db.session.commit()

            if current_status is not None and current_status is not monitor.status:
                print("STATUS CHANGED. SENDING EMAIL")
                send_email(monitor, email, username)
