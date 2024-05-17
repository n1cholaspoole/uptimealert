from flask import Blueprint, render_template, abort, request, flash, url_for, redirect
from flask_login import current_user, login_required
from models import Dashboard, Monitor, DashboardMonitor
from forms import DashForm, DashMonitorForm
from jinja2 import TemplateNotFound
from app import db

dash = Blueprint('dash', __name__, template_folder='templates')


@dash.route('/dash/', methods=['GET', 'POST'])
@login_required
def dashboards():
    form = DashForm(request.form)
    if request.method == 'GET':
        try:
            user_dashboards = (Dashboard.query.filter_by(user_id=current_user.id)
                               .options(db.joinedload(Dashboard.monitors).joinedload(DashboardMonitor.monitor)).all())
            user_monitors = Monitor.query.filter_by(user_id=current_user.id).all()
            db.session.close()

            return render_template('/dash/dashboards.html',
                                   user_dashboards=user_dashboards, user_monitors=user_monitors)
        except TemplateNotFound:
            abort(404)
    elif request.method == 'POST':
        if form.validate():
            try:
                dashboard = Dashboard.query.filter_by(name=form.name.data.strip(), user_id=current_user.id).first()

                if dashboard:
                    flash('Страница состояния с таким названием уже существует.')
                    return render_template('/dash/dashboards.html', form=form)

                new_dashboard = Dashboard(name=form.name.data.strip(), user_id=current_user.id)

                db.session.add(new_dashboard)
                db.session.commit()
                db.session.close()

                return redirect(url_for('dash.dashboards'))
            except TemplateNotFound:
                abort(404)
        flash("Validation error")
        print(form.errors)
        return render_template('/dash/dashboards.html', form=form)
    else:
        abort(404)


@dash.route('/dash/monitor/add/', methods=['POST'])
@login_required
def dashboards_monitor_add():
    form = DashMonitorForm(request.form)
    if request.method == 'POST':
        dashboard_monitor = (Dashboard.query.filter_by(id=form.dashboard_id.data, user_id=current_user.id)
                             .filter(Dashboard.monitors.any(DashboardMonitor.monitor_id == form.monitor_id.data))
                             .first())

        if dashboard_monitor:
            flash('Этот монитор уже существует на странице.')
            return render_template('/dash/dashboards.html', form=form)

        new_dashboard_monitor = DashboardMonitor(dashboard_id=form.dashboard_id.data, monitor_id=form.monitor_id.data)

        db.session.add(new_dashboard_monitor)
        db.session.commit()
        db.session.close()

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


def get_monitors_by_dash_id(dashboard_id):
    user_dashboard_monitors = (Monitor.query.join(DashboardMonitor)
                               .filter(DashboardMonitor.dashboard_id == dashboard_id)
                               .order_by(Monitor.status, Monitor.name).all())
    db.session.close()

    return user_dashboard_monitors


@dash.route('/dash/<int:dashboard_id>/', methods=['GET'])
@login_required
def dashboard(dashboard_id):
    if request.method == 'GET':
        try:
            user_dashboard_monitors = get_monitors_by_dash_id(dashboard_id)

            return render_template('/dash/dashboard.html', user_dashboard_monitors=user_dashboard_monitors)
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
            user_dashboard_monitors = get_monitors_by_dash_id(dashboard_id)

            return render_template('/dash/dashboard_partial.html',
                                   user_dashboard_monitors=user_dashboard_monitors)
        except TemplateNotFound:
            abort(404)
    else:
        abort(405)
