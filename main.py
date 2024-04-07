import os
import smtplib
import uuid
from functools import wraps
from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_bootstrap import Bootstrap5
from flask_gravatar import Gravatar
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, ForeignKey
from flask_ckeditor import CKEditor
from datetime import date
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
Bootstrap5(app)
ckeditor = CKEditor(app)

gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False,
                    base_url=None)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(UserData, user_id)


class Base(DeclarativeBase):
    pass


# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'


app.config[
    'SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI")
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class UserData(UserMixin, db.Model):  # parent
    __tablename__ = "users_data"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, unique=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(100), default="commentor")
    password_hash: Mapped[str] = mapped_column(String(1000), nullable=False)
    blog_post = relationship("BlogPost", back_populates="user")
    comment = relationship("Comment", back_populates="user")


class BlogPost(db.Model):
    __tablename__ = "blogs_post"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    subtitle: Mapped[str] = mapped_column(String(250), nullable=False)
    date: Mapped[str] = mapped_column(String(250), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(250), nullable=False)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users_data.user_id"))
    user = relationship("UserData", back_populates="blog_post")
    comment = relationship("Comment", back_populates="blog_post", cascade="all, delete")


class Comment(db.Model):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author: Mapped[str] = mapped_column(String(250), nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users_data.user_id"))
    comment: Mapped[str] = mapped_column(String(250), nullable=False)
    post_id: Mapped[str] = mapped_column(ForeignKey("blogs_post.id"))
    blog_post = relationship("BlogPost", back_populates="comment")
    user = relationship("UserData", back_populates="comment")


with app.app_context():
    db.create_all()


def admin_only(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("login"))
        if current_user.role == 'admin':
            return function(*args, **kwargs)
        else:
            return abort(403)

    return wrapper


def send_mail(name, email, mobile, message):
    my_email = os.environ.get("EMAIL")
    password = os.environ.get("PASSWORD")
    with smtplib.SMTP("smtp.gmail.com:587") as connection:
        connection.starttls()

        connection.login(user=my_email, password=password)
        mail_result = connection.sendmail(from_addr=my_email, to_addrs=os.environ.get("RECEIVER"),
                                          msg=f"Subject:Message from {name}\n\nHi this is {name}.{message} "
                                              f"\nYou can also contact me on {mobile} or at {email}")
    print(mail_result)


@app.route('/')
def get_all_posts():
    posts = db.session.query(BlogPost).order_by(BlogPost.id.desc()).all()
    return render_template("index.html", all_posts=posts[0:4])


@app.route('/old_posts')
def get_old_posts():
    posts = db.session.query(BlogPost).order_by(BlogPost.id.desc()).all()
    return render_template("index.html", all_posts=posts[4:])


@app.route('/register', methods=["GET", "POST"])
def register():
    if current_user.is_authenticated is True and current_user.role != "admin":
        return redirect(url_for('get_all_posts'))

    form = RegisterForm()
    if request.method == "POST":
        user_data = request.form.to_dict()
        user = UserData()
        user.name = user_data.get("name")
        user.email = user_data.get("email").lower()
        password = user_data.get("password")

        check_user_data = db.session.query(UserData).filter(UserData.email == user.email).first()
        if check_user_data:
            flash(message="User already present, Please login")
            return render_template("register.html", form=form)

        password_hash = generate_password_hash(password, method="pbkdf2", salt_length=16)
        user.password_hash = password_hash
        user.user_id = uuid.uuid4().hex
        if current_user.is_authenticated is True and current_user.role == "admin":
            user.role = "admin"
            db.session.add(user)
            db.session.commit()
        else:
            db.session.add(user)
            db.session.commit()
            login_user(user)
        return redirect(url_for('get_all_posts'))
    return render_template("register.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    if current_user.is_authenticated is True:
        return redirect(url_for('get_all_posts'))

    form = LoginForm()

    if request.method == "POST":
        user_data = request.form.to_dict()
        email = user_data.get("email").lower()
        password = user_data.get("password")
        check_user_data = db.session.query(UserData).filter(UserData.email == email).first()

        if check_user_data is None:
            flash(message="User not found, please register first")
            return render_template("login.html", form=form)
        check_password = check_password_hash(check_user_data.password_hash, password)

        if check_password:
            login_user(check_user_data)
            return redirect(url_for('get_all_posts'))
        else:
            flash(message="Wrong password, please try again")
    return render_template("login.html", form=form)


@app.route('/get_blogs_by_name/<author_id>')
def get_blogs_by_name(author_id):
    data = db.session.query(BlogPost).filter(BlogPost.author_id == author_id).all()
    return render_template("index.html", all_posts=data, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/show_post/<post_id>', methods=["GET", "POST"])
@login_required
def show_post(post_id):
    form = CommentForm()
    blog_post = db.session.query(BlogPost).filter(BlogPost.id == post_id).first()
    if request.method == "POST":
        comment = Comment()
        comment.blog_post = blog_post
        comment.user = current_user
        comment.comment = request.form.to_dict().get("comment")
        comment.author = current_user.name
        db.session.add(comment)
        db.session.commit()
        return redirect(url_for('show_post', post_id=post_id))
    return render_template("post.html", post=blog_post, form=form, comments=blog_post.comment)


@app.route('/add', methods=["GET", "POST"])
@admin_only
def add_new_post():
    post = CreatePostForm()
    if request.method == 'POST':
        form_data = request.form.to_dict()
        blogpost = BlogPost()
        for key, value in form_data.items():
            setattr(blogpost, key, value)
        blogpost.author = current_user.name
        today_date = date.today().strftime('"%B %d, %Y"')
        blogpost.user = current_user
        blogpost.date = today_date
        with app.app_context():
            db.session.add(blogpost)
            db.session.commit()
        return redirect(url_for('get_all_posts'))

    return render_template("make-post.html", post=post, title="")


@app.route("/edit_post/<post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    blogpost = db.session.query(BlogPost).filter(BlogPost.id == post_id).first()
    post = CreatePostForm(title=blogpost.title, subtitle=blogpost.subtitle, author=blogpost.author, body=blogpost.body,
                          img_url=blogpost.img_url)
    if request.method == "POST":
        form_data = request.form.to_dict()
        for key, value in form_data.items():
            setattr(blogpost, key, value)
        db.session.commit()
        return redirect(url_for('get_all_posts'))
    return render_template("make-post.html", post=post, title=blogpost.title)


@app.route("/delete_post/<post_id>")
@admin_only
def delete_post(post_id):
    blogpost = db.session.query(BlogPost).filter(BlogPost.id == post_id).first()
    db.session.delete(blogpost)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        data = request.form.to_dict()
        send_mail(name=data.get("name"), email=data.get("email"), mobile=data.get("phone"), message=data.get("message"))
        flash(message="Thank You, I will be in touch shortly.")

    return render_template("contact.html")


if __name__ == "__main__":
    app.run(debug=True, port=5003)
