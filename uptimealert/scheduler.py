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
    header = f'Alert! {monitor.name} is {state}'
    body = (f"Hi, {username}. Your monitor {monitor.name}\n"
            f"is {state} after {monitor.failed_times} checks, since our last check at {timestamp}")

    if monitor.status:
        state = "UP"
        body = (f"Hi, {username}. Your monitor {monitor.name}\n"
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
                if monitor.status != current_status:
                    monitor.status = current_status
                    monitor.failed_times = 0

                    print(f"{monitor.id} | Monitor is UP. Sending email...")
                    send_email(monitor, email, username)
            else:
                monitor.failed_times += 1
                if monitor.failed_times == monitor.threshold:
                    monitor.status = current_status

                    print(f"{monitor.id} | FAILED {monitor.failed_times} times out of {monitor.threshold}. "
                          f"Sending email...")
                    send_email(monitor, email, username)
                else:
                    print(f"{monitor.id} | FAILED {monitor.failed_times} times out of {monitor.threshold}")

            db.session.commit()