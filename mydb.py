from models import User, Game, GameInfo, GameDownload, SharedFile
from models import db
from datetime import date

from mysecurity import myhash, verify, encode
import uuid


def save_to_db(instance):
    db.session.add(instance)
    db.session.commit()


# Юзеры

def post_login(username, password):

    user = User.query.filter_by(username=username).first()
    print(user)

    if not user:
        raise ValueError('Такого аккаунта не существует')

    password = myhash(password)
    if not user.password == password:
        raise ValueError('Пароль не подходит')

    token = encode(username)
    return token

def get_users_all():
    return User.query.all()

def get_users_one(username):
    user = User.query.filter_by(username=username).first()
    return user.anonim() if user else None

def post_register(username, password):

    # Проверки перед отправкой
    if not username or not password:
        raise ValueError("Заполните все поля")
    
    existing_user = User.query.filter_by(username = username).first()
    if existing_user:
        raise ValueError("Аккаунт с таким именем уже существует")
    
    if len(username) < 3:
        raise ValueError("Юзернейм должен быть от 3 символов")
    
    if len(password) < 5:
        raise ValueError("Пароль должен быть от 5 символов")

    password = myhash(password)

    user = User(username = username, password = password)
    save_to_db(user)

    return user


# Приложения

def get_apps_all():
    return Game.query.filter_by(is_archived=False).all()

def get_app_one(link):
    games = get_apps_all()
    return next((game for game in games if game.link == link), None)

def get_app_by_user(username):
    games = get_apps_all()
    return [game for game in games if game.game_info and game.game_info.published_by == username]

# def post_comment(userid, gameid, text):
#     game_comment = GameComment(
#         gameid = gameid,
#         userid = userid,
        
#         text = text,
#     )
#     save_to_db(game_comment)

def post_game(
        title, link, comments_allowed, preview,
        # GameInfo
        description, price, release_date, language, published_by,
        # GameDownload
        file):
    game = Game(
        title=title,
        preview=preview,
        link=link,
        comments_allowed=comments_allowed,
        is_archived=False,
    )
    save_to_db(game)

    game_info = GameInfo(
        game_id=game.id,
        description=description,
        price=price,
        release_date=release_date,
        language=language,
        published_by=published_by,
    )
    save_to_db(game_info)

    print("Game created:", game)
    return game


def add_game_download(game_id, title, file_link, order=0):
    game_download = GameDownload(game_id=game_id, title=title, file_link=file_link, order=order)
    save_to_db(game_download)

    return game_download

def archive_game(game):
    game.is_archived = True
    print(game.is_archived)
    db.session.commit()

def get_files_all():
    return SharedFile.query.all()

def get_files_one(link):
    file = SharedFile.query.filter_by(link=link).first()
    return file

def post_file(title, preview, file_link, link, uploaded_by):
    shared_file = SharedFile(
        title=title,
        preview=preview,
        file_link=file_link,
        uploaded_by=uploaded_by,
        is_active=True,
        expires=30,
        auto_download=0,
        link=link
        # link="file-" + uuid.uuid4().hex[:10]
    )
    save_to_db(shared_file)

    view_url = f"{shared_file.link}"
    print("File shared:", shared_file)
    return view_url