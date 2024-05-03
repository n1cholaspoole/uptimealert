from flask import Blueprint, render_template, abort, request, flash, url_for, redirect
from wtforms import Form, StringField, SelectField, IntegerRangeField, IntegerField, validators
from flask_login import current_user, login_required
from models import Monitor
from jinja2 import TemplateNotFound
from app import db
from datetime import datetime

main = Blueprint('main', __name__, template_folder='templates')


class MonitorForm(Form):
    name = StringField('Friendly name', [validators.Length(max=50)])
    type = SelectField('Type', choices=[('ping', 'PING'), ('port', 'PORT'), ('http', 'HTTP')])
    schema = SelectField('Schema', choices=[('https://', 'https://'), ('http://', 'http://')],
                         validators=[validators.Optional()])
    hostname = StringField('Hostname', [validators.Length(max=100)])
    port = IntegerField('Port', [validators.Optional(),
                                 validators.NumberRange(0, 65535)])
    interval = IntegerRangeField('Interval', [validators.NumberRange(1, 60)])
    threshold = IntegerRangeField('Threshold', [validators.NumberRange(1, 10)])

    def validate(self):
        if not super(MonitorForm, self).validate():
            return False
        if self.type.data == "http" and self.schema.data is None:
            self.schema.errors.append("Schema is required.")
            return False
        elif self.type.data == "port" and self.port.data is None:
            self.port.errors.append("Port is required.")
            return False
        return True


@main.route('/')
def index():
    return render_template('/main/index.html')


@main.route('/profile')
@login_required
def profile():
    return render_template('/main/profile.html', username=current_user.username)


@main.route('/dash')
@login_required
def dashboard():
    return render_template('/main/dashboard.html')


@main.route('/monitors', methods=['GET', 'POST'])
@login_required
def monitors():
    form = MonitorForm(request.form)
    if request.method == 'GET':
        try:
            user_monitors = Monitor.query.filter_by(user_id=current_user.id).order_by(Monitor.status).all()
            db.session.close()

            if user_monitors:
                for monitor in user_monitors:
                    if monitor.last_checked_at:
                        monitor.last_checked_at = monitor.last_checked_at.strftime("%d-%m-%Y %H:%M")

                    if monitor.status:
                        monitor.status = "Up"
                    elif monitor.status is None:
                        monitor.status = "Yet unknown"
                    else:
                        monitor.status = "Down"

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


@main.route('/monitors/<int:monitor_id>/delete', methods=['POST'])
@login_required
def monitors_delete(monitor_id):
    if request.method == 'POST':
        user_monitor = Monitor.query.filter_by(id=monitor_id).first()

        if monitor_id and user_monitor.user_id is current_user.id:
            db.session.delete(user_monitor)
            db.session.commit()
            db.session.close()

        return redirect(url_for('main.monitors'))
    else:
        abort(405)


@main.route('/monitors/<int:monitor_id>', methods=['GET'])
@login_required
def monitors_id(monitor_id):
    if request.method == 'GET':
        try:
            user_monitor = Monitor.query.filter_by(id=monitor_id).first()
            db.session.close()

            if user_monitor.user_id is not current_user.id:
                return redirect(url_for('main.monitors'))

            return render_template('/main/monitor.html', user_monitor=user_monitor)
        except TemplateNotFound:
            abort(404)
    else:
        abort(405)
