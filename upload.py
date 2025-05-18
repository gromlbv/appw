import os
from werkzeug.utils import secure_filename
from flask import current_app
from dataclasses import dataclass
import uuid

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


@dataclass
class File():
    name: str
    path: str
    size: int


def upload_file(file, folder='static/uploads'):
    if not file:
        return None

    ext = os.path.splitext(file.filename)[1]
    file_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(current_app.root_path, folder, file_name)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    file.save(file_path)

    file_size = os.path.getsize(file_path)

    new_file = File(
        name = file_name,
        path = file_name,
        size = file_size
    )

    return new_file