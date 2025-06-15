import os
import uuid
import shutil
import zipfile

from flask import current_app
from dataclasses import dataclass
# from werkzeug.utils import secure_filename


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_image(file, folder='static/uploads'):
    if not file:
        return None

    if not allowed_file(file.filename):
        return None

    ext = os.path.splitext(file.filename)[1]
    file_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(current_app.root_path, folder, file_name)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    file.save(file_path)

    return f"{folder}/{file_name}"


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



def upload_unity_build(file, game_id, folder='static/uploads/unity_archives'):
    if not file:
        return None

    ext = os.path.splitext(file.filename)[1].lower()
    if ext != '.zip':
        raise ValueError("Unity сборка должна лежать в архиве (.zip)")

    file_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(current_app.root_path, folder, file_name)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    file.save(file_path)

    file_size = os.path.getsize(file_path)

    unpack_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'unity_builds', str(game_id))

    if os.path.exists(unpack_dir):
        shutil.rmtree(unpack_dir)
    os.makedirs(unpack_dir, exist_ok=True)

    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(unpack_dir)

    # Можно удалить архив, если не нужен
    # os.remove(file_path)

    new_file = File(
        name=file_name,
        path=f"uploads/unity_builds/{game_id}/index.html",
        size=file_size
    )

    return new_file
