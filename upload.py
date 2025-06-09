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





import os
import uuid
import zipfile
import shutil
from flask import current_app

def upload_unity_build(file, game_id, folder='static/uploads/unity_archives'):
    if not file:
        return None

    ext = os.path.splitext(file.filename)[1].lower()
    if ext != '.zip':
        return None  # или кинуть ошибку

    file_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(current_app.root_path, folder, file_name)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    file.save(file_path)

    file_size = os.path.getsize(file_path)

    # Папка для распаковки
    unpack_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'unity_builds', str(game_id))

    # Очистить, если есть
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
