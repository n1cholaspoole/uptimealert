from urllib.parse import urlparse

from flask import Blueprint, render_template, abort, request, flash, url_for, redirect
from flask_login import current_user, login_required
from models import Monitor, User, SharedMonitor, DashboardMonitor
from forms import MonitorForm, ShareForm
from jinja2 import TemplateNotFound
from app import db
from datetime import datetime
import socket
import idna
import re

mnts = Blueprint('mnts', __name__, template_folder='templates')


def strip_protocol(url):
    new_url = re.sub(r'^[a-zA-Z]+:/{1,3}', '', url)
    return new_url


def is_ip_address(address):
    try:
        return socket.inet_aton(address)

    except socket.error:
        try:
            socket.inet_pton(socket.AF_INET6, address)
            return True

        except socket.error:
            return False


def is_valid_hostname(hostname):
    if len(hostname) > 255:
        return False

    try:
        idna_encoded = idna.encode(hostname).decode('ascii')
    except idna.IDNAError:
        return False

    allowed = re.compile(r"^(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in idna_encoded.split("."))


def is_valid_url(url):
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname

    if hostname is None:
        return False, False

    return is_ip_address(hostname), is_valid_hostname(hostname)


@mnts.route('/monitors/', methods=['GET', 'POST'])
@login_required
def monitors():
    form = MonitorForm(request.form)
    if request.method == 'GET':
        try:
            user_monitors = Monitor.query.filter_by(user_id=current_user.id).order_by(Monitor.status,
                                                                                      Monitor.name).all()
            shared_monitors = (db.session.query(SharedMonitor).join(Monitor, SharedMonitor.monitor_id == Monitor.id)
                               .filter(SharedMonitor.shared_user_id == current_user.id)
                               .options(db.joinedload(SharedMonitor.monitor))
                               .order_by(Monitor.status, Monitor.name).all())

            db.session.close()

            return render_template('/mnts/monitors.html',
                                   user_monitors=user_monitors, shared_monitors=shared_monitors)
        except TemplateNotFound:
            abort(404)
    elif request.method == 'POST':
        if form.validate():
            try:
                monitor = Monitor.query.filter_by(name=form.name.data.strip()).first()

                if monitor and monitor.user_id is current_user.id:
                    flash('Монитор с таким названием уже существует.', 'monitor')

                schema = form.schema.data
                hostname = form.hostname.data.strip()

                if form.type.data in ['ping', 'port']:
                    if not is_ip_address(hostname) and not is_valid_hostname(hostname):
                        flash('Поле "Имя хоста" должно содержать только IP-адрес или домен.',
                              'monitor')
                        return redirect(url_for('mnts.monitors'))

                if form.type.data == 'http':
                    if not is_valid_url(hostname):
                        flash('Проверьте введенный URL-адрес.', 'monitor')
                        return redirect(url_for('mnts.monitors'))
                    hostname = strip_protocol(hostname)
                else:
                    form.schema.data = None

                new_monitor = Monitor(name=form.name.data.strip(), type=form.type.data,
                                      schema=schema, hostname=hostname,
                                      port=form.port.data, interval=form.interval.data,
                                      threshold=form.threshold.data, created_at=datetime.now(),
                                      user_id=current_user.id)

                db.session.add(new_monitor)
                db.session.commit()
                db.session.close()

                return redirect(url_for('mnts.monitors'))
            except TemplateNotFound:
                abort(404)
        else:
            flash("Ошибка валидации формы.", 'monitor')
            print(form.errors)
        return redirect(url_for('mnts.monitors'))
    else:
        abort(405)


@mnts.route('/monitors/<int:monitor_id>/delete/', methods=['POST'])
@login_required
def monitors_delete(monitor_id):
    if request.method == 'POST':
        user_monitor = Monitor.query.filter_by(id=monitor_id, user_id=current_user.id).first()

        if user_monitor:
            db.session.delete(user_monitor)
            db.session.commit()
            db.session.close()

        return redirect(url_for('mnts.monitors'))
    else:
        abort(405)


@mnts.route('/monitors/<int:monitor_id>/toggle/', methods=['POST'])
@login_required
def monitors_toggle(monitor_id):
    if request.method == 'POST':
        user_monitor = Monitor.query.filter_by(id=monitor_id, user_id=current_user.id).first()

        if user_monitor:
            if user_monitor.disabled:
                user_monitor.disabled = False
            else:
                user_monitor.disabled = True

            db.session.commit()
            db.session.close()

        return redirect(url_for('mnts.monitors'))
    else:
        abort(405)


@mnts.route('/monitors/share/', methods=['POST'])
@login_required
def monitors_share():
    form = ShareForm(request.form)
    if request.method == 'POST':
        if form.validate():
            user = User.query.filter_by(email=form.email.data.strip()).first()
            monitor = Monitor.query.filter_by(id=form.hidden_id.data, user_id=current_user.id).first()

            if not user:
                flash('Пользователя с таким адресом электронной почты не существует.', 'share')
            elif user.email is current_user.email:
                flash('Поделитесь с кем-нибудь другим.', 'share')
            else:
                if monitor:
                    shared_monitor = SharedMonitor.query.filter_by(shared_user_id=user.id,
                                                                   monitor_id=monitor.id).first()
                    if shared_monitor:
                        flash('Этот пользователь уже имеет доступ.', 'share')
                    else:
                        new_shared_monitor = SharedMonitor(monitor_id=monitor.id, shared_user_id=user.id)

                        db.session.add(new_shared_monitor)
                        db.session.commit()

            db.session.close()
            return redirect(url_for('mnts.monitor', monitor_id=form.hidden_id.data))
        else:
            flash("Ошибка валидации формы.")
            print(form.errors)
        return redirect(url_for('mnts.monitors'))
    else:
        abort(405)


@mnts.route('/monitors/<int:monitor_id>/share/<int:share_id>/delete/', methods=['POST'])
@login_required
def monitors_share_delete(share_id, monitor_id):
    if request.method == 'POST':
        share = ((db.session.query(SharedMonitor).join(Monitor, Monitor.id == SharedMonitor.monitor_id)
                  .filter(SharedMonitor.id == share_id)
                  .filter((Monitor.user_id == current_user.id) | (SharedMonitor.shared_user_id == current_user.id))
                  .options(db.joinedload(SharedMonitor.monitor))
                  .first()))

        if share:
            dashboard_monitors = (db.session.query(DashboardMonitor)
                                  .filter(DashboardMonitor.monitor_id == share.monitor_id).all())

            for dashboard_monitor in dashboard_monitors:
                db.session.delete(dashboard_monitor)
            db.session.delete(share)
            db.session.commit()

        db.session.close()
        return redirect(url_for('mnts.monitor', monitor_id=monitor_id))
    else:
        abort(405)


@mnts.route('/monitors/<int:monitor_id>/', methods=['GET'])
@login_required
def monitor(monitor_id):
    if request.method == 'GET':
        try:
            user_monitor = (db.session.query(Monitor)
                            .options(db.joinedload(Monitor.shared_users).joinedload(SharedMonitor.shared_user),
                                     db.joinedload(Monitor.incidents))
                            .filter(Monitor.id == monitor_id, Monitor.user_id == current_user.id).first())

            if not user_monitor:
                return redirect(url_for('mnts.monitors'))

            db.session.close()
            return render_template('/mnts/monitor.html', user_monitor=user_monitor)
        except TemplateNotFound:
            abort(404)
    else:
        abort(405)


@mnts.route('/monitors/shared/<int:monitor_id>/', methods=['GET'])
@login_required
def monitor_shared(monitor_id):
    if request.method == 'GET':
        try:
            shared_monitor = (db.session.query(Monitor)
                              .options(db.joinedload(Monitor.shared_users).joinedload(SharedMonitor.shared_user),
                                       db.joinedload(Monitor.incidents), db.joinedload(Monitor.user))
                              .filter(Monitor.id == monitor_id, SharedMonitor.shared_user_id == current_user.id)
                              .first())

            if not shared_monitor:
                return redirect(url_for('mnts.monitors'))

            db.session.close()
            return render_template('/mnts/monitor_shared.html', shared_monitor=shared_monitor)
        except TemplateNotFound:
            abort(404)
    else:
        abort(405)
