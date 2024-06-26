from init_celery import celery
from app import db
from app import mail
from models import Monitor, User, Incident, SharedMonitor
from datetime import datetime, timedelta
from flask_mail import Message
from contextlib import closing
import requests
import subprocess
import socket


def check_socket(host, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        return sock.connect_ex((host, port)) == 0


def sender(monitor, username, email):
    timestamp = monitor.last_checked_at.strftime("%d-%m-%Y %H:%M:%S")

    state = "НЕДОСТУПЕН"
    header = f'Тревога! {monitor.name} {state}'
    body = (f"{username}, ваш монитор {monitor.name} "
            f"больше {state} после {monitor.failed_times} проверок, время последней проверки {timestamp}")

    if monitor.status:
        state = "ДОСТУПЕН"
        header = f'{monitor.name} снова {state}'
        body = (f"{username}, ваш монитор {monitor.name} "
                f"снова {state} после нашей последней проверки в {timestamp}")

    msg = Message(header, body=body, recipients=[email])
    mail.send(msg)


def send_email(monitor):
    sender(monitor, monitor.user.username, monitor.user.email)
    for share in monitor.shared_users:
        sender(monitor, share.shared_user.username, share.shared_user.email)


@celery.task
def ping(monitor_id):
    now = datetime.now()
    timestamp = now.strftime("%d-%m-%Y %H:%M:%S")
    current_status = None

    monitor = (db.session.query(Monitor).filter(Monitor.id == monitor_id).join(User, Monitor.user_id == User.id)
               .options(db.joinedload(Monitor.shared_users).joinedload(SharedMonitor.shared_user)).first())

    if monitor:
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
                response = requests.get(f"{monitor_url}", timeout=5)
                if response.ok or response.is_redirect:
                    current_status = True
                else:
                    current_status = False
                print(f"{monitor.id} | HTTP | {timestamp} | {current_status} | {response.status_code}")
            except requests.RequestException as e:
                current_status = False
                print(f"{monitor.id} | HTTP | {timestamp} | {current_status} | Exception")
                print(f"Encountered exception: {e}")

        if monitor.status is None:
            monitor.status = current_status

        if current_status:
            monitor.failed_times = 0

            if monitor.status != current_status:
                monitor.status = current_status

                incident = Incident.query.filter_by(monitor_id=monitor.id).order_by(
                    Incident.created_at.desc()).first()
                if incident and incident.resolved_at is None:
                    incident.resolved_at = now
                    print("Incident resolved.")
                else:
                    print("Incident resolved, but its record appears to be deleted.")

                print(f"{monitor.id} | Monitor is UP. Sending email...")
                send_email(monitor)
        else:

            if monitor.failed_times <= monitor.threshold:
                monitor.failed_times += 1
                db.session.commit()

                print(f"{monitor.id} | FAILED {monitor.failed_times} times out of {monitor.threshold}")

                if monitor.failed_times == monitor.threshold:
                    monitor.status = current_status

                    print("Recording new incident...")
                    new_incident = Incident(monitor_id=monitor.id, created_at=now)

                    db.session.add(new_incident)

                    print("Sending email...")
                    send_email(monitor)
                else:
                    db.session.close()
                    print("Retrying immediately...")
                    ping.delay(monitor_id)

    db.session.commit()
    db.session.close()


@celery.task
def ping_servers():
    print(f"SCHEDULER IS RUNNING")

    now = datetime.now()
    next_minute = now + timedelta(minutes=1)

    monitors = (db.session.query(Monitor).join(User, Monitor.user_id == User.id)
                .options(db.joinedload(Monitor.shared_users).joinedload(SharedMonitor.shared_user)).all())

    for monitor in monitors:
        if not monitor.disabled:
            if monitor.last_checked_at is None or next_minute > monitor.last_checked_at + timedelta(
                    minutes=monitor.interval):
                ping.delay(monitor.id)

    db.session.close()
