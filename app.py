import logging
from flask import Flask
from flask_admin import Admin
from sqlalchemy import select
from db import db
from models.posts import Posts
from sqlalchemy.event import listens_for
import os
import os.path as op
from flask_admin.contrib import sqla
from flask import url_for
from flask_admin import form
from markupsafe import Markup
from wtforms.validators import InputRequired, DataRequired 
from utils.helper import generate_unique_filename, remove_file_from_s3, upload_file_to_s3
from sqlalchemy.sql import text


from wtforms import fields, widgets

app = Flask(__name__, static_folder="files")

# set optional bootswatch theme
app.config["FLASK_ADMIN_SWATCH"] = "cosmo"
app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://admin:admin@postgres/admin"
app.config["SECRET_KEY"] = "klOLCFB99Kl6o1PJn6zgQDm60jOrre8h"
app.config["SQLALCHEMY_ECHO"] = True
db.init_app(app)
with app.app_context():
    db.create_all()
admin = Admin(app, name="GarageDoorsAdminPanel", template_mode="bootstrap3")


# Create directory for file fields to use
file_path = op.join(op.dirname(__file__), "files")
try:
    os.mkdir(file_path)
except OSError:
    pass


# define a custom wtforms widget and field.
# see https://wtforms.readthedocs.io/en/latest/widgets.html#custom-widgets
class CKTextAreaWidget(widgets.TextArea):
    def __call__(self, field, **kwargs):
        # add WYSIWYG class to existing classes
        existing_classes = kwargs.pop("class", "") or kwargs.pop("class_", "")
        kwargs["class"] = "{} {}".format(existing_classes, "ckeditor")
        return super(CKTextAreaWidget, self).__call__(field, **kwargs)


class CKTextAreaField(fields.TextAreaField):
    widget = CKTextAreaWidget()


class ImageView(sqla.ModelView):
    def _list_thumbnail(view, context, model, name):
        if not model.path:
            return ""

        return Markup(
            '<img src="%s">'
            % url_for('static', filename=form.thumbgen_filename(model.path))
        )

    form_args = {
        "post_date": {"validators": [InputRequired()]},
    }

    

    column_formatters = {"path": _list_thumbnail}
    
    form_extra_fields = {
        "path": form.ImageUploadField(
            "Image",
            base_path=file_path,
            thumbnail_size=(100, 100, True),
            validators=[DataRequired()],
            namegen=generate_unique_filename,
        )
    }

    form_overrides = {
        'text': CKTextAreaField
    }

    create_template = "create_page.html"
    edit_template = "edit_page.html"


    # Alternative way to contribute field is to override it completely.
    # In this case, Flask-Admin won't attempt to merge various parameters for the field.


@listens_for(Posts, "after_delete")
def del_image(mapper, connection, target):
    if target.path:
        # Delete image
        try:
            os.remove(op.join(file_path, target.path))
            remove_file_from_s3(target.path)
        except OSError:
            pass

        # Delete thumbnail
        try:
            os.remove(op.join(file_path, form.thumbgen_filename(target.path)))
        except OSError:
            pass


@listens_for(Posts, 'after_insert')
def receive_after_insert(mapper, connection, target):
    try:
        with open(op.join(file_path, target.path), 'rb') as file:
            upload_file_to_s3(file)
    except OSError:
        pass

@listens_for(Posts, 'after_update')
def receive_after_update(mapper, connection, target):
    try:
        with open(op.join(file_path, target.path), 'rb') as file:
            upload_file_to_s3(file)
    except OSError:
        pass

@listens_for(Posts, 'before_update')
def receive_before_update(mapper, connection, target):
    old_row = db.session.execute(text(f"SELECT * FROM Posts WHERE id = {target.id}")).fetchone()
    try:
        remove_file_from_s3(old_row.path)
    except OSError:
        pass


admin.add_view(ImageView(Posts, db.session))


def get_posts_from_db():
    rows = db.session.execute(db.select(Posts.path, Posts.text, Posts.post_date)).fetchall()
    result = [row._asdict() for row in rows]
    return result


# Add administrative views here
# Flask views
@app.route("/")
def index():
    return '<a href="/admin">Click me to get to Admin!</a>'


@app.route("/posts")
def send_posts():
    posts = get_posts_from_db()
    result = {
        "data": posts,
        "AWS_DOMAIN": os.getenv("AWS_DOMAIN")
    }
    return result


if __name__ == "__main__":
    # Start app
    app.run(debug=True)
