from init_celery import celery
from app import db
from app import mail
from models import Monitor, User, Incident
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
    header = f'Alert! {monitor.name} is {state}'
    body = (f"Hi, {username}. Your monitor {monitor.name} "
            f"is {state} after {monitor.failed_times} checks, since our last check at {timestamp}")

    if monitor.status:
        state = "UP"
        header = f'Alert! {monitor.name} is {state}'
        body = (f"Hi, {username}. Your monitor {monitor.name} "
                f"is {state} since our last check at {timestamp}")

    msg = Message(header, body=body, recipients=[email])
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

        if monitor.last_checked_at is None or next_minute > monitor.last_checked_at + timedelta(
                minutes=monitor.interval):
            monitor.last_checked_at = now

            if monitor.type == "ping":
                current_status = subprocess.call(['ping', '-c', '1', monitor.hostname]) == 0
                print(f"{monitor.id} | PING | {timestamp} | {current_status}")
            elif monitor.type == "port":
                current_status = check_socket(monitor.hostname, monitor.port)
                print(f"{monitor.id} | PORT | {timestamp} | {current_status}")
            elif monitor.type == "http":
                try:
                    monitor_url = monitor.schema + monitor.hostname
                    response = requests.get(f"{monitor_url}", timeout=10)
                    if response.ok or response.is_redirect:
                        current_status = True
                    else:
                        current_status = False
                    print(f"{monitor.id} | HTTP | {timestamp} | {current_status} | {response.status_code}")
                except requests.RequestException:
                    current_status = False
                    print(f"{monitor.id} | HTTP | {timestamp} | {current_status} | Exception")

            if monitor.status is None:
                monitor.status = current_status

            if current_status:
                monitor.failed_times = 0

                if monitor.status != current_status:
                    monitor.status = current_status

                    incident = Incident.query.filter_by(monitor_id=monitor.id).order_by(
                        Incident.created_at.desc()).first()
                    if incident:
                        incident.resolved_at = now
                        print("Incident resolved.")

                    db.session.commit()

                    print(f"{monitor.id} | Monitor is UP. Sending email...")
                    send_email(monitor, email, username)
            else:
                monitor.failed_times += 1
                db.session.commit()

                print(f"{monitor.id} | FAILED {monitor.failed_times} times out of {monitor.threshold}")

                if monitor.failed_times == monitor.threshold:
                    monitor.status = current_status

                    print("Recording new incident...")
                    new_incident = Incident(monitor_id=monitor.id, created_at=now)

                    db.session.add(new_incident)
                    db.session.commit()

                    print("Sending email...")
                    send_email(monitor, email, username)

    db.session.commit()
    db.session.close()
