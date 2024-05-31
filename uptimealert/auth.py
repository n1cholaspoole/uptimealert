from flask import Blueprint, render_template, abort, url_for, request, flash, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from models import User
from forms import SignUpForm, LoginForm
from jinja2 import TemplateNotFound
from app import db

auth = Blueprint('auth', __name__, template_folder='templates', url_prefix='/auth')


@auth.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'GET':
        try:
            return render_template('/auth/login.html', form=form)
        except TemplateNotFound:
            abort(404)
    elif request.method == 'POST':
        if form.validate():
            try:
                remember = True if form.password.data else False

                user = User.query.filter_by(email=form.email.data).first()
                db.session.close()

                if not user or not check_password_hash(user.password, form.password.data):
                    flash('Проверьте свои учетные данные и попробуйте еще раз.', 'login')
                    return render_template('/auth/login.html', form=form)

                login_user(user, remember=remember)
                return redirect(url_for('mnts.monitors'))
            except TemplateNotFound:
                abort(404)
        else:
            flash('Ошибка валидации формы', 'login')
            print(form.errors)
        return redirect(url_for('auth.login'))
    else:
        abort(405)


@auth.route('/signup/', methods=['GET', 'POST'])
def signup():
    form = SignUpForm(request.form)
    if request.method == 'GET':
        try:
            return render_template('/auth/signup.html', form=form)
        except TemplateNotFound:
            abort(404)
    elif request.method == 'POST':
        if form.validate():
            try:
                user = User.query.filter_by(email=form.email.data).first()

                if user:
                    flash('Аккаунт с такой электронной почтой уже существует.', 'signup')
                    return render_template('/auth/signup.html', form=form)

                new_user = User(email=form.email.data, username=form.username.data,
                                password=generate_password_hash(form.password.data, method='pbkdf2:sha256'))
                db.session.add(new_user)
                db.session.commit()
                db.session.close()

                flash('Спасибо за регистрацию.', 'login_s')
                return redirect(url_for('auth.login'))
            except TemplateNotFound:
                abort(404)
        else:
            flash('Ошибка валидации формы', 'signup')
            print(form.errors)
        return redirect(url_for('auth.signup'))
    else:
        abort(405)


@auth.route('/logout/')
@login_required
def logout():
    try:
        logout_user()
        return redirect(url_for('main.index'))
    except TemplateNotFound:
        abort(404)
