from models import User, Game, GameInfo, GameDownload, SharedFile, GameStats
from models import db
from datetime import date
from mysecurity import myhash, verify, encode
import uuid
from sqlalchemy.orm import joinedload


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

def get_shares_all():
    return Game.query.filter_by(is_archived=False).all()

def get_app_one(link):
    apps = get_shares_all()
    return next((game for game in apps if game.link == link), None)

def get_latest(limit):
    return Game.query\
        .join(GameInfo)\
        .filter(Game.is_archived == False)\
        .order_by(GameInfo.updated_at.desc())\
        .limit(limit)\
        .all()

def get_all_apps():
    return [game for game in get_shares_all() if game.info and game.info.app_type == 'app']

def get_all_games():
    return [game for game in get_shares_all() if game.info and game.info.app_type == 'game']


def get_app_by_user(username):
    apps = get_shares_all()
    result = []
    for game in apps:
        if game.info and game.info.published_by == username:
            result.append(game)
    return result

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
        description, price, release_date, language, published_by, app_type, category,
        ):
    
    if not title or not link:
        return ("Некоторые поля не заполнены")
    
    if link in [game.link for game in get_shares_all()]:
        return (f"Ссылка {link} уже используется")
    
    game = Game(
        title=title,
        preview=preview,
        link=link,
        comments_allowed=comments_allowed,
        is_archived=False,
    )
    save_to_db(game)

    info = GameInfo(
        game_id=game.id,
        description=description,
        price=price,
        release_date=release_date,
        language=language,
        published_by=published_by,
        app_type=app_type,
        category=category
    )
    save_to_db(info)

    print("Game created:", game)
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
        game.stats = GameStats(game_id=game.id)
        db.session.add(game.stats)
    stats = game.stats
    stats.serious_fun = serious_fun
    stats.utility_gamified = utility_gamified
    db.session.commit()
    return True

def create_sample_games():
    sample_data = [
        # Игры
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

        # Программы
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
        game = Game(title=title, link=link)
        db.session.add(game)
        db.session.flush()

        stats = GameStats(
            game_id=game.id,
            serious_fun=serious_fun,
            utility_gamified=utility_gamified
        )
        db.session.add(stats)

    db.session.commit()

def get_download_info(filename):
    game_download = db.session.query(GameDownload).filter_by(file_link=filename).first()
    game = db.session.query(Game).filter_by(id=game_download.game_id).first()

    game_name = game.title
    title = game_download.title
    file_link = game_download.file_link
    extension = '.' + file_link.rsplit('.', 1)[-1]

    if title:
        download_name = game_name + " · " + title + extension
    else:
        download_name = game_name+ extension
    return download_name

def add_game_download(game_id, title, file_link, file_size, order=0):
    game_download = GameDownload(game_id=game_id, title=title, file_link=file_link, file_size=file_size, order=order)
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



