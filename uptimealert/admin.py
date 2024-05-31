from flask import Blueprint, render_template, abort, request, flash, redirect, url_for
from werkzeug.security import generate_password_hash
from flask_login import current_user, login_required
from models import User
from jinja2 import TemplateNotFound
from forms import AdminForm
from app import db

admin = Blueprint('admin', __name__, template_folder='templates', url_prefix='/admin')


@admin.route('/chpasswd/', methods=['GET', 'POST'])
@login_required
def chpasswd():
    form = AdminForm(request.form)
    if request.method == 'GET':
        try:
            if current_user.id == 1:
                users = User.query.all()
                db.session.close()

                return render_template('/admin/chpasswd.html', users=users)
            return redirect(url_for('main.index'))
        except TemplateNotFound:
            abort(404)
    elif request.method == 'POST':
        if form.validate():
            if current_user.id == 1:
                user = User.query.filter(User.id == form.user_id.data).first()

                if not user:
                    flash('Аккаунта не существует', 'admin')
                else:
                    User.query.filter_by(id=form.user_id.data).update(
                        {User.password: generate_password_hash(form.password.data, method='pbkdf2:sha256')})
                    db.session.commit()
                    db.session.close()
                    flash('Пароль успешно изменен.', 'admin_s')

                return redirect(url_for('admin.chpasswd'))

            return redirect(url_for('main.index'))
        else:
            flash("Ошибка валидации формы.", 'admin')
            print(form.errors)
        return redirect(url_for('admin.chpasswd'))
    else:
        abort(405)