from flask import Blueprint, render_template, abort, request, flash, url_for, redirect
from flask_login import current_user, login_required
from models import User
from forms import EmailForm, UsernameForm
from app import db

main = Blueprint('main', __name__, template_folder='templates')


@main.route('/', methods=['GET'])
def index():
    return render_template('/main/index.html')


@main.route('/profile/', methods=['GET'])
@login_required
def profile():
    return render_template('/main/profile.html', username=current_user.username)


@main.route('/profile/change/email', methods=['POST'])
@login_required
def profile_change_email():
    form = EmailForm(request.form)
    if request.method == 'POST':
        if form.validate():
            user = User.query.filter(User.email == form.email.data.strip(), User.id != current_user.id).first()

            if user:
                flash('Аккаунт с такой электронной почтой уже существует.', 'email')
            else:
                User.query.filter_by(id=current_user.id).update({User.username: form.email.data})
                db.session.commit()
                db.session.close()
        else:
            flash("Ошибка валидации формы.", 'email')
            print(form.errors)
        return redirect(url_for('main.profile'))
    else:
        abort(405)


@main.route('/profile/change/username', methods=['POST'])
@login_required
def profile_change_username():
    form = UsernameForm(request.form)
    if request.method == 'POST':
        if form.validate():
            User.query.filter_by(id=current_user.id).update({User.username: form.username.data.strip()})
            db.session.commit()
            db.session.close()
        else:
            flash("Ошибка валидации формы.", 'username')
            print(form.errors)
        return redirect(url_for('main.profile'))
    else:
        abort(405)
