from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy import func

from models import User, Game, GameInfo, GameDownload, SharedFile, GameStats, Collection, CollectionUser, CollectionGame
from models import db

from mysecurity import myhash, verify, encode



def save_to_db(instance):
    db.session.add(instance)
    db.session.commit()

# Юзеры

def post_login(username, password):
    user = User.query.filter_by(username=username).first()

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

    user = User()
    user.username = username
    user.password = password

    save_to_db(user)

    return user


# Приложения

def get_shares_all():
    return Game.query.filter_by(is_archived=False).order_by(Game.id.desc()).all()


def get_all_apps():
    return [game for game in get_shares_all() if game.info and game.info.app_type == 'app']

def get_all_games():
    return [game for game in get_shares_all() if game.info and game.info.app_type == 'game']


def get_shares_search(query):
    results = (
        Game.query.filter_by(is_archived=False)
        .filter(func.lower(Game.title).like(f"%{query.lower()}%"))
        .limit(10)
        .all()
    )
    return results

def get_app_one(link):
    apps = get_shares_all()
    return next((game for game in apps if game.link == link), None)

def get_latest(limit):
    latest_apps = Game.query\
        .join(GameInfo)\
        .filter(
            Game.is_archived == False,
            GameInfo.updated_at.isnot(None)
        )\
        .order_by(GameInfo.updated_at.desc())\
        .limit(limit)\
        .all()
    return latest_apps


def get_app_by_user(username):
    apps = get_shares_all()
    result = []
    for game in apps:
        if game.info and game.info.published_by == username:
            result.append(game)
    return result

def get_app_by_id(link):
    return Game.query.filter_by(link=link).first()


def post_game_edit(
        game_id, title, link, comments_allowed, is_unity_build, external_link, preview,
        description, price, release_date, language, published_by, app_type, category,
    ):
    game = Game.query.get(game_id)
    
    if not game:
        return f"Игра с ID {game_id} не найдена"

    if not title or not link:
        return "Некоторые поля не заполнены"

    
    link = link.lower()
        
    game.title = title
    game.link = link
    game.comments_allowed = comments_allowed
    game.is_unity_build = is_unity_build
    game.external_link = external_link
    game.preview = preview

    save_to_db(game)

    info = GameInfo.query.filter_by(game_id=game_id).first()
    if not info:
        info = GameInfo()
        info.game_id = game_id

    info.description = description
    info.price = price
    info.release_date = release_date
    info.language = language
    info.published_by = published_by
    info.updated_at = func.now()
    info.app_type = app_type
    info.category = category

    save_to_db(info)

    return game



import utils

def post_game(
        title, link, comments_allowed, is_unity_build, external_link, preview,
        # GameInfo
        description, price, release_date, language, published_by, app_type, category,
        ):
    
    if not title or not link:
        raise ValueError('Некоторые поля не заполнены')
    
    utils.validate_link(link)
        
    game = Game()
    game.title = title
    game.preview = preview
    game.link = link
    game.comments_allowed = comments_allowed
    game.is_unity_build = is_unity_build
    game.external_link = external_link
    game.is_archived = False

    try:
        save_to_db(game)
    except IntegrityError:
        db.session.rollback()
        raise ValueError('Ссылка уже используется')

    info = GameInfo()
    info.game_id = game.id
    info.description = description
    info.price = price
    info.release_date = release_date
    info.language = language
    info.published_by = published_by
    info.updated_at = func.now()
    info.app_type = app_type
    info.category = category

    save_to_db(info)

    return game

def get_all_games_with_stats():
    games = get_shares_all()
    game_ids = [game.id for game in games]
    games_with_stats = Game.query.options(joinedload(Game.stats)).filter(Game.id.in_(game_ids)).all()
    return games_with_stats

def update_game_stats(game_id, serious_fun, utility_gamified):
    game = Game.query.get(game_id)
    if not game:
        return False
    if not game.stats:
        game.stats = GameStats()
        game.stats.game_id = game_id
        db.session.add(game.stats)
    stats = game.stats
    stats.serious_fun = serious_fun
    stats.utility_gamified = utility_gamified
    db.session.commit()
    return True

def create_sample_games():
    sample_data = [
        ("Arma 3", "arma3", 15, 94),
        ("Roblox", "roblox", 98, 96),
        ("Minecraft", "minecraft", 91, 100),
        ("CS:GO", "csgo", 38, 97),
        ("Fortnite", "fortnite", 94, 100),
        ("The Sims 4", "sims4", 64, 93),
        ("GTA V", "gta5", 94, 98),
        ("Factorio", "factorio", 36, 90),
        ("RimWorld", "rimworld", 43, 91),
        ("Kerbal Space Program", "kerbal", 67, 93),

        ("Paint", "paint", 52, 13),
        ("After Effects", "after_effects", 2, 0),
        ("Photoshop", "photoshop", 23, 0),
        ("Notepad++", "notepadpp", 5, 0),
        ("Premiere Pro", "premiere_pro", 0, 0),
        ("Blender", "blender", 25, 9),
        ("Visual Studio Code", "vscode", 3, 0),
        ("FL Studio", "flstudio", 10, 18),
        ("Unity", "unity", 14, 56),
        ("DaVinci Resolve", "davinci_resolve", 5, 5),
    ]

    for title, link, serious_fun, utility_gamified in sample_data:
        game = Game()
        game.title = title
        game.link = link
        
        db.session.add(game)
        db.session.flush()

        stats = GameStats()
        stats.game_id = game.id
        stats.serious_fun = serious_fun
        stats.utility_gamified = utility_gamified
        
        db.session.add(stats)

    db.session.commit()

def get_download_info(filename):
    game_download = db.session.query(GameDownload).filter_by(file_link=filename).first()
    if game_download is None:
        return None
    game = db.session.query(Game).filter_by(id=game_download.game_id).first()

    if game is None:
        return None
    
    game_name = game.title
    title = game_download.title
    file_link = game_download.file_link
    extension = '.' + file_link.rsplit('.', 1)[-1]

    if title:
        download_name = game_name + " · " + title + extension
    else:
        download_name = game_name+ extension
    return download_name

def game_add_download(game_id, title, description, file_link, file_size, order=0):
    game_download = GameDownload()
    game_download.game_id = game_id
    game_download.title = title
    game_download.description = description
    game_download.file_link = file_link
    game_download.file_size = file_size
    game_download.order = order

    save_to_db(game_download)

    return game_download

def archive_game(game):
    game.is_archived = True
    print(game.is_archived)
    db.session.commit()

def delete_game(game_id):
    game = Game.query.get(game_id)
    if game:
        db.session.delete(game)
        db.session.commit()
        return True
    return False


# Коллекции

import uuid

def coll_get():
    collections = Collection.query.all()
    return collections

def coll_get_one(link):
    collection = Collection.query.filter_by(link=link).first()
    return collection

def coll_get_by_user(user_id):
    collections = Collection.query.filter_by(owner_id=user_id).all()
    return collections

def coll_get_by_user_edit(user_id):
    edited = Collection.query.join(CollectionUser)\
        .filter(CollectionUser.user_id == user_id, CollectionUser.can_edit == True)\
        .all()

    return edited

def coll_get_not_added_users(link):
    coll = Collection.query.filter_by(link=link).first_or_404()
    added_ids = [cu.user_id for cu in coll.members]  # <-- members, не users

    if added_ids:
        users = User.query.filter(~User.id.in_(added_ids)).all()
    else:
        users = User.query.all()

    return users


def invite_user_to_collection(coll_id, user_id, can_edit=False, can_view=False, invited_by=None):
    new_member = CollectionUser()
    new_member.collection_id = coll_id
    new_member.user_id = user_id
    new_member.can_edit = can_edit
    new_member.can_view = can_view
    new_member.invited_by = invited_by
    save_to_db(new_member)


def coll_post(title, owner_id):
    collection = Collection()
    collection.title = title
    collection.owner_id = owner_id
    collection.link = uuid.uuid4().hex

    save_to_db(collection)

    return collection.link

def coll_game_add(collection_id, game_id):
    collection_game = CollectionGame()
    collection_game.collection_id = collection_id
    collection_game.game_id = game_id

    save_to_db(collection_game)

    return collection_game

def coll_add_user(collection_id, user_id, can_edit):
    collection_user = CollectionUser()
    collection_user.collection_id = collection_id
    collection_user.user_id = user_id
    collection_user.can_edit = can_edit

    save_to_db(collection_user)

    return collection_user

def coll_delete(collection_id):
    collection = Collection.query.get(collection_id)
    if collection:
        db.session.delete(collection)
        db.session.commit()
        return True
    return False

def coll_get_not_added_games(link):
    coll = Collection.query.filter_by(link=link).first_or_404()
    added_ids = [cg.game_id for cg in coll.games.all()]
    
    if added_ids:
        return Game.query.filter(~Game.id.in_(added_ids)).all()
    else:
        return Game.query.all()

def coll_remove_app(collection_id, game_id):
    CollectionGame.query.filter_by(collection_id=collection_id, game_id=game_id).delete()
    db.session.commit()




def get_files_all():
    return SharedFile.query.all()

def get_files_one(link):
    file = SharedFile.query.filter_by(link=link).first()
    return file

def post_file(title, preview, file_link, link, uploaded_by):
    shared_file = SharedFile()
    shared_file.title = title
    shared_file.preview = preview
    shared_file.file_link = file_link
    shared_file.uploaded_by = uploaded_by
    shared_file.is_active = True
    shared_file.expires = 30
    shared_file.auto_download = 0
    shared_file.link = link
    save_to_db(shared_file)

    view_url = f"{shared_file.link}"
    return view_url



# def post_comment(userid, gameid, text):
#     game_comment = GameComment(
#         gameid = gameid,
#         userid = userid,
        
#         text = text,
#     )
#     save_to_db(game_comment)