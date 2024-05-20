from wtforms import Form, StringField, SelectField, IntegerRangeField, IntegerField, PasswordField, validators


class SignUpForm(Form):
    username = StringField('Username', [validators.Length(min=3, max=50)])
    email = StringField('Email Address', [validators.Email(), validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.Length(min=8, max=100),
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Пароли должны совпадать.')
    ])
    confirm = PasswordField('Repeat Password')


class LoginForm(Form):
    email = StringField('Email Address', [validators.Email(), validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.Length(min=8, max=100),
        validators.DataRequired()
    ])


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
            self.schema.errors.append("Схема обязательна.")
            return False
        elif self.type.data == "port" and self.port.data is None:
            self.port.errors.append("Порт обязателен.")
            return False
        return True


class MonitorAdminForm(MonitorForm):
    owner_id = IntegerField('Owner ID', [validators.NumberRange()])


class DashForm(Form):
    name = StringField('Friendly name', [validators.Length(min=1, max=100)])


class DashMonitorForm(Form):
    dashboard_id = IntegerField('Dashboard ID', [validators.NumberRange()])
    monitor_id = IntegerField('Monitor ID', [validators.NumberRange()])


class EmailForm(Form):
    email = StringField('Email Address', [validators.Email(), validators.Length(min=6, max=50)])


class UsernameForm(Form):
    username = StringField('Username', [validators.Length(min=3, max=50)])


class ShareForm(Form):
    hidden_id = IntegerField('Hidden ID', [validators.NumberRange()])
    email = StringField('Email Address', [validators.Email(), validators.Length(min=6, max=50)])