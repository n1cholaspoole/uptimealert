from flask import Blueprint, render_template, abort, request, flash, url_for, redirect
from flask_login import current_user, login_required
from models import Dashboard, Monitor, DashboardMonitor, SharedMonitor, User
from forms import DashForm, DashMonitorForm
from jinja2 import TemplateNotFound
from app import db

dash = Blueprint('dash', __name__, template_folder='templates')


class DashboardInfo:
    def __init__(self, dashboard, owned_monitors, shared_monitors):
        self.dashboard = dashboard
        self.owned_monitors = owned_monitors
        self.shared_monitors = shared_monitors


@dash.route('/dash/', methods=['GET', 'POST'])
@login_required
def dashboards():
    form = DashForm(request.form)
    if request.method == 'GET':
        try:
            user_monitors = db.session.query(Monitor).filter_by(user_id=current_user.id).all()

            shared_monitors = (db.session.query(Monitor, User.email.label('email'))
                               .join(SharedMonitor, Monitor.id == SharedMonitor.monitor_id)
                               .join(User, Monitor.user_id == User.id)
                               .filter(SharedMonitor.shared_user_id == current_user.id).all())

            user_dashboards = Dashboard.query.filter_by(user_id=current_user.id).all()

            dashboards = []

            for dashboard in user_dashboards:
                owned_monitors = (db.session.query(Monitor)
                                  .join(DashboardMonitor, Monitor.id == DashboardMonitor.monitor_id)
                                  .filter(DashboardMonitor.dashboard_id == dashboard.id,
                                          Monitor.user_id == current_user.id)
                                  .all())

                dash_shared_monitors = (db.session.query(Monitor, User.email.label('email'))
                                   .join(SharedMonitor, Monitor.id == SharedMonitor.monitor_id)
                                   .join(DashboardMonitor, Monitor.id == DashboardMonitor.monitor_id)
                                   .join(User, Monitor.user_id == User.id)
                                   .filter(DashboardMonitor.dashboard_id == dashboard.id,
                                           SharedMonitor.shared_user_id == current_user.id)
                                   .all())

                dashboards.append(DashboardInfo(dashboard, owned_monitors, dash_shared_monitors))

            db.session.close()

            return render_template('/dash/dashboards.html', dashboards=dashboards,
                                   user_monitors=user_monitors, shared_monitors=shared_monitors)
        except TemplateNotFound:
            abort(404)
    elif request.method == 'POST':
        if form.validate():
            try:
                dashboard = Dashboard.query.filter_by(name=form.name.data.strip(), user_id=current_user.id).first()

                if dashboard:
                    flash('Страница состояния с таким названием уже существует.', 'dash')
                else:
                    new_dashboard = Dashboard(name=form.name.data.strip(), user_id=current_user.id)

                    db.session.add(new_dashboard)
                    db.session.commit()
                    db.session.close()

                return redirect(url_for('dash.dashboards'))
            except TemplateNotFound:
                abort(404)
        else:
            flash('Ошибка валидации формы', 'dash')
            print(form.errors)
        return redirect(url_for('dash.dashboards'))
    else:
        abort(404)


@dash.route('/dash/monitor/add/', methods=['POST'])
@login_required
def dashboards_monitor_add():
    form = DashMonitorForm(request.form)
    if request.method == 'POST':
        if form.validate():
            dashboard_monitor = (Dashboard.query.filter_by(id=form.dashboard_id.data, user_id=current_user.id)
                                 .filter(Dashboard.monitors.any(DashboardMonitor.monitor_id == form.monitor_id.data))
                                 .first())

            if dashboard_monitor:
                flash('Этот монитор уже существует на странице.', 'monitor')
            else:
                new_dashboard_monitor = DashboardMonitor(dashboard_id=form.dashboard_id.data,
                                                         monitor_id=form.monitor_id.data)

                db.session.add(new_dashboard_monitor)
                db.session.commit()
                db.session.close()

        else:
            flash("Ошибка валидации формы.", 'monitor')
            print(form.errors)
        return redirect(url_for('dash.dashboards'))
    else:
        abort(405)


@dash.route('/dash/<int:dashboard_id>/monitor/<int:monitor_id>/delete/', methods=['POST'])
@login_required
def dashboards_monitor_delete(dashboard_id, monitor_id):
    if request.method == 'POST':
        user_monitor = (DashboardMonitor.query.join(Dashboard)
                        .filter(Dashboard.id == dashboard_id, Dashboard.user_id == current_user.id,
                                DashboardMonitor.monitor_id == monitor_id).first())

        if user_monitor:
            db.session.delete(user_monitor)
            db.session.commit()
            db.session.close()

        return redirect(url_for('dash.dashboards'))
    else:
        abort(405)


def get_monitors_by_dash_id(dashboard_id, current_user_id):
    user_dashboard_monitors = (Monitor.query.join(DashboardMonitor)
                               .filter(DashboardMonitor.dashboard_id == dashboard_id,
                                       Monitor.user_id == current_user_id)
                               .order_by(Monitor.status, Monitor.name).all())
    shared_dashboard_monitors = (Monitor.query.join(DashboardMonitor, Monitor.id == DashboardMonitor.monitor_id)
                                 .join(SharedMonitor, Monitor.id == SharedMonitor.monitor_id)
                                 .filter(DashboardMonitor.dashboard_id == dashboard_id,
                                         SharedMonitor.shared_user_id == current_user.id)
                                 .order_by(Monitor.status, Monitor.name).all())

    db.session.close()

    return user_dashboard_monitors, shared_dashboard_monitors


@dash.route('/dash/<int:dashboard_id>/', methods=['GET'])
@login_required
def dashboard(dashboard_id):
    if request.method == 'GET':
        try:
            user_dashboard_monitors, shared_dashboard_monitors = get_monitors_by_dash_id(dashboard_id, current_user.id)

            if user_dashboard_monitors or shared_dashboard_monitors:
                return render_template('/dash/dashboard.html',
                                       user_dashboard_monitors=user_dashboard_monitors,
                                       shared_dashboard_monitors=shared_dashboard_monitors)

            return redirect(url_for("dash.dashboards"))
        except TemplateNotFound:
            abort(404)
    else:
        abort(405)


@dash.route('/dash/<int:dashboard_id>/delete/', methods=['POST'])
@login_required
def dashboards_delete(dashboard_id):
    if request.method == 'POST':
        user_dashboard = Dashboard.query.filter_by(id=dashboard_id, user_id=current_user.id).first()

        if dashboard_id:
            db.session.delete(user_dashboard)
            db.session.commit()
            db.session.close()

        return redirect(url_for('dash.dashboards'))
    else:
        abort(405)


@dash.route('/dash/<int:dashboard_id>/update_partial/', methods=['GET'])
@login_required
def dash_get_monitors(dashboard_id):
    if request.method == 'GET':
        try:
            user_dashboard_monitors, shared_dashboard_monitors = get_monitors_by_dash_id(dashboard_id, current_user.id)

            if user_dashboard_monitors or shared_dashboard_monitors:
                return render_template('/dash/dashboard_partial.html',
                                       user_dashboard_monitors=user_dashboard_monitors,
                                       shared_dashboard_monitors=shared_dashboard_monitors)

            return redirect(url_for("dash.dashboards"))
        except TemplateNotFound:
            abort(404)
    else:
        abort(405)
