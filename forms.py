from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.fields.simple import URLField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


class CreatePostForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = URLField("Image URL", validators=[DataRequired()])
    body = CKEditorField("Body", validators=[DataRequired()])
    submit = SubmitField("Submit")


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password = StringField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = StringField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")


# TODO: Create a CommentForm so users can leave comments below posts
class CommentForm(FlaskForm):
    comment = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit")
