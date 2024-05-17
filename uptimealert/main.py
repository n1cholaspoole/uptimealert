from flask import Blueprint, render_template, abort, request, flash, url_for, redirect
from flask_login import current_user, login_required
from models import Monitor, Incident
from forms import MonitorForm
from jinja2 import TemplateNotFound
from app import db
from datetime import datetime

main = Blueprint('main', __name__, template_folder='templates')


@main.route('/')
def index():
    return render_template('/main/index.html')


@main.route('/profile/')
@login_required
def profile():
    return render_template('/main/profile.html', username=current_user.username)


@main.route('/monitors/', methods=['GET', 'POST'])
@login_required
def monitors():
    form = MonitorForm(request.form)
    if request.method == 'GET':
        try:
            user_monitors = Monitor.query.filter_by(user_id=current_user.id).order_by(Monitor.status,
                                                                                      Monitor.name).all()
            db.session.close()

            return render_template('/main/monitors.html', user_monitors=user_monitors)
        except TemplateNotFound:
            abort(404)
    elif request.method == 'POST':
        if form.validate():
            try:
                monitor = Monitor.query.filter_by(name=form.name.data.strip()).first()

                if monitor and monitor.user_id is current_user.id:
                    flash('Monitor with this name already exists')
                    return render_template('/main/monitors.html', form=form)

                if form.type.data != 'http':
                    form.schema.data = None

                new_monitor = Monitor(name=form.name.data.strip(), type=form.type.data,
                                      schema=form.schema.data, hostname=form.hostname.data,
                                      port=form.port.data, interval=form.interval.data,
                                      threshold=form.threshold.data, created_at=datetime.now(),
                                      user_id=current_user.id)

                db.session.add(new_monitor)
                db.session.commit()
                db.session.close()

                return redirect(url_for('main.monitors'))
            except TemplateNotFound:
                abort(404)
        flash("Validation error")
        print(form.errors)
        return render_template('/main/monitors.html', form=form)
    else:
        abort(405)


@main.route('/monitors/<int:monitor_id>/delete/', methods=['POST'])
@login_required
def monitors_delete(monitor_id):
    if request.method == 'POST':
        user_monitor = Monitor.query.filter_by(id=monitor_id, user_id=current_user.id).first()

        if monitor_id:
            db.session.delete(user_monitor)
            db.session.commit()
            db.session.close()

        return redirect(url_for('main.monitors'))
    else:
        abort(405)


@main.route('/monitors/<int:monitor_id>/', methods=['GET'])
@login_required
def monitor(monitor_id):
    if request.method == 'GET':
        try:
            user_monitor = Monitor.query.filter_by(id=monitor_id, user_id=current_user.id).first()
            monitors_incidents = Incident.query.filter_by(monitor_id=monitor_id).all()
            db.session.close()

            if not user_monitor:
                return redirect(url_for('main.monitors'))

            return render_template('/main/monitor.html',
                                   user_monitor=user_monitor, monitors_incidents=monitors_incidents)
        except TemplateNotFound:
            abort(404)
    else:
        abort(405)
