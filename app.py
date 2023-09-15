from datetime import datetime

from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   url_for)
from flask_bcrypt import Bcrypt
from flask_login import (LoginManager, UserMixin, current_user, login_required,
                         login_user, logout_user)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length

app = Flask(__name__)

# Используем SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.secret_key = 'fdfghj'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    # Определение отношения к модели Task
    tasks = db.relationship('Task')

    # Методы для Flask-Login
    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def has_liked(self, task_id):
        return Like.query.filter_by(user_id=self.id, task_id=task_id).first() is not None


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User", back_populates="tasks")

    def __init__(self, title, description, user_id):
        self.title = title
        self.description = description
        self.user_id = user_id

    def is_liked_by(self, user):
        return Like.query.filter_by(user_id=user.id, task_id=self.id).first() is not None

    def count_likes(self):
        return Like.query.filter_by(task_id=self.id).count()


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)


from wtforms import ValidationError

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[
                           DataRequired(), Length(min=4, max=80)])
    password = PasswordField('Пароль', validators=[
                             DataRequired(), Length(min=8, max=120)])
    submit = SubmitField('Зарегистрироваться')

    def validate_password(self, field):
        if len(field.data) < 8:
            raise ValidationError('Пароль должен содержать не менее 8 символов.')



from wtforms import ValidationError

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[
                           DataRequired(), Length(min=4, max=80)])
    password = PasswordField('Пароль', validators=[
                             DataRequired(), Length(min=8, max=120)])
    submit = SubmitField('Войти')

    def validate_password(self, field):
        if len(field.data) < 8:
            raise ValidationError('Пароль должен содержать не менее 8 символов.')



from wtforms import StringField, TextAreaField, validators

class TaskForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired(), Length(min=4, max=100)])
    description = TextAreaField('Описание', validators=[Length(max=200)])

    def validate_title(self, field):
        # Пример кастомной валидации: убедитесь, что название задачи уникально для каждого пользователя
        user_id = current_user.id  # Предполагается, что у вас есть объект current_user
        existing_task = Task.query.filter_by(title=field.data, user_id=user_id).first()
        if existing_task:
            raise ValidationError('Задача с таким заголовком уже существует.')


@app.route('/')
def index():
    # Здесь можно вернуть главную страницу вашего блога
    return render_template('index.html')


login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data.encode(
            'utf-8')  # Кодируем пароль в байты

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash('Имя пользователя уже занято. Пожалуйста, выберите другое.', 'danger')
        else:
            # Хешируем пароль
            hashed_password = bcrypt.generate_password_hash(password)

            new_user = User(username=username, password=hashed_password.decode(
                'utf-8'))  # Декодируем хеш и сохраняем строку
            db.session.add(new_user)
            db.session.commit()
            flash('Регистрация успешно завершена! Теперь вы можете войти в систему.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Вход выполнен успешно', 'success')
            next_page = request.args.get('next')
            # Перенаправление на страницу аккаунта или другую страницу, если указана
            return redirect(next_page or url_for('account'))

        flash('Ошибка входа. Проверьте ваше имя пользователя и пароль..', 'danger')

    return render_template('login.html', form=form)


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = TaskForm()  # Создайте экземпляр формы для создания задач

    if form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        task = Task(title=title, description=description,
                    user_id=current_user.id)
        db.session.add(task)
        db.session.commit()
        flash('Задача успешно создана.', 'success')
        return redirect(url_for('account'))

    tasks = Task.query.filter_by(user_id=current_user.id).order_by(
        Task.created_at.desc()).all()
    return render_template('account.html', tasks=tasks, form=form)


@app.route('/tasks', methods=['GET', 'POST'])
@login_required
def tasks():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        task = Task(title=title, description=description,
                    user_id=current_user.id)
        db.session.add(task)
        db.session.commit()

    tasks = Task.query.join(User).all()
    return render_template('tasks.html', tasks=tasks)


@app.route('/like/<int:task_id>', methods=['POST'])
@login_required
def like(task_id):
    task = Task.query.get_or_404(task_id)
    existing_like = Like.query.filter_by(
        user_id=current_user.id, task_id=task.id).first()

    if existing_like:
        # Если лайк уже существует, удаляем его (снимаем лайк)
        db.session.delete(existing_like)
        liked = False  # Лайк был снят
        user = None  # Пользователя нет, так как лайк снят
    else:
        # Если лайка нет, создаем новый
        like = Like(user_id=current_user.id, task_id=task.id)
        db.session.add(like)
        liked = True  # Лайк был установлен
        user = current_user  # Текущий пользователь установил лайк

    db.session.commit()

    # Возвращаем JSON-ответ с обновленным количеством лайков и информацией о пользователе
    likes_count = Like.query.filter_by(task_id=task.id).count()
    return jsonify({'likes': likes_count, 'liked': liked, 'user': user.username if user else None})




@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
