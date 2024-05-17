from flask import Blueprint, render_template, abort, request
from flask_login import current_user, login_required
from models import Monitor
from jinja2 import TemplateNotFound
from app import db

admin = Blueprint('admin', __name__, template_folder='templates', url_prefix='/admin')


@admin.route('/monitors', methods=['GET'])
@login_required
def monitors_admin():
    if request.method == 'GET':
        try:
            if current_user.id == 1:
                users_monitors = Monitor.query.order_by(Monitor.status).all()
                db.session.close()

                if users_monitors:
                    for monitor in users_monitors:
                        if monitor.last_checked_at:
                            monitor.last_checked_at = monitor.last_checked_at.strftime("%d-%m-%Y %H:%M")

                        if monitor.status:
                            monitor.status = "Доступен"
                        elif monitor.status is None:
                            monitor.status = "Пока неизвестно"
                        else:
                            monitor.status = "Недоступен"

                return render_template('/admin/monitors.html', users_monitors=users_monitors)
        except TemplateNotFound:
            abort(404)
    else:
        abort(405)
