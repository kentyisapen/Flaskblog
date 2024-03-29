from flask import Flask, render_template, redirect, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
import pytz
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = os.urandom(24)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login', error="ログインしてください"))


tags = db.Table('tags',
                db.Column('tag_id', db.Integer, db.ForeignKey(
                    'tag.id'), primary_key=True),
                db.Column('post_id', db.Integer, db.ForeignKey(
                    'post.id'), primary_key=True)
                )


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(20))
    posts = db.relationship('Post', backref="user", lazy=True)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tags = db.relationship('Tag', secondary="tags",
                           lazy='subquery', backref=db.backref('posts', lazy=True))
    title = db.Column(db.String(50), nullable=False)
    body = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.now(pytz.timezone("Asia/Tokyo")))


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/", methods=["GET"])
def index():  # index関数の定義
    posts = Post.query.all()
    return render_template("index.html", posts=posts)


@app.route("/article1")
def article1():  # article1関数の定義　
    return render_template("article1.html")


@app.route("/article2")
def article2():  # article2関数の定義
    return render_template("article2.html")


@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        title = request.form.get("title")
        body = request.form.get("body")
        user_id = current_user.id
        post = Post(title=title, body=body, user_id=user_id)

        db.session.add(post)
        db.session.commit()
        return redirect("/")
    else:
        return render_template("create.html")


@app.route("/<int:id>/update", methods=["GET", "POST"])
@login_required
def update(id):
    post = Post.query.get(id)
    if current_user.id != post.user_id:
        return redirect(url_for('index', error="アクセス権がありません"))

    if request.method == "GET":
        return render_template("update.html", post=post)
    else:
        post.title = request.form.get("title")
        post.body = request.form.get("body")
        db.session.commit()
        return redirect("/")


@app.route("/<int:id>/delete", methods=["GET"])
@login_required
def delete(id):
    post = Post.query.get(id)
    if current_user.id != post.user_id:
        return redirect(url_for('index', error="アクセス権がありません"))

    db.session.delete(post)
    db.session.commit()
    return redirect("/")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User(username=username, password=generate_password_hash(
            password, method="sha256"))
        db.session.add(user)
        db.session.commit()
        return redirect("/login")
    else:
        return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if check_password_hash(user.password, password):
            login_user(user)
            return redirect("/")
    else:
        return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


if __name__ == '__main__':
    app.run(debug=True)
