import os
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_image(file, folder='static/uploads'):
    if not file:
        return None

    if not allowed_file(file.filename):
        return None

    filename = secure_filename(file.filename)
    filepath = os.path.join(current_app.root_path, folder, filename)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    file.save(filepath)

    return f"{folder}/{filename}"


def upload_file(file, folder='static/uploads'):
    if not file:
        return None

    # if not allowed_file(file.filename):
    #     print(f"File {file.filename} is not allowed.")
    #     return None

    filename = secure_filename(file.filename)
    filepath = os.path.join(current_app.root_path, folder, filename)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    file.save(filepath)

    return f"{folder}/{filename}"