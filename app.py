from flask import Flask
from flask import render_template, session, request, flash, redirect, jsonify
from flask import url_for as furl_for
from routes import *

from models import create_app, create_tables
from mysecurity import verify, decode
from upload import upload_image, upload_file

import mydb as db
from datetime import datetime

app = Flask(__name__)
create_app(app)

app.secret_key = 'rulevsecretkey'


@app.route('/form')
def form():
    return render_template('form.html')
    
    
def is_loggined():
    print('Проверяю токен')
    if 'token' in session:
        user_token = session['token']
        print('Токен найден', user_token)
        if verify(user_token) == False:
            print('Токен ГОВНО', user_token)
            session.pop('token', None)
        else:
            return True
    return False

def get_user_id():
    user_token = session.get('token')
    if not user_token:
        return None
    user_id = decode(user_token)
    return user_id

@app.template_filter('filesize')
def filesize_filter(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


@app.get('/')
def index():
    shares = db.get_shares_all()
    games = db.get_all_games()
    apps = db.get_all_apps()
    latest_shares = db.get_latest(4)
    
    return render_template(
        "index.html",
        users=db.get_users_all(),
        shares=shares,
        games=games,
        apps=apps,
        latest_shares=latest_shares,
        files=db.get_files_all(),
        is_loggined=is_loggined(),
        user_id=get_user_id()
    )

@app.get('/graphs')
def graphs():
    games = db.get_shares_all()  # список объектов Game

    apps = []
    for game in games:
        print(game)
        print(game.game_downloads[0].file_size) if game.game_downloads else print(0)
        size = game.game_downloads[0].file_size if game.game_downloads else 0
        apps.append({
            'link': game.link,
            'title': game.title,
            'size': size
        })

    print(apps)
    return render_template(
        "graphs.html",
        users=db.get_users_all(),
        apps=apps,
        games=games,
    )


@app.route('/api/get-categories')
def get_categories():
    app_type = request.args.get('type')
    if app_type == 'game':
        categories = ["Шутер", "Головоломка", "RPG", "Приключения", "Кооператив", "Симулятор"]
    elif app_type == 'app':
        categories = ["Мессенджер", "Утилита", "Фото", "Образование"]
    else:
        categories = []

    return jsonify({'categories': categories})


@app.get('/game/create')
def add_game():
    return render_template('add_game.html')

@app.post('/game/create')
def post_game():
    title = request.form.get('title')
    link = request.form.get('link')

    game_file = request.files.get('game_file')
    game_file = upload_file(game_file)

    image_file = request.files.get('image_file')
    preview = upload_image(image_file)

    description = request.form.get('description')
    price = request.form.get('price')

    release_date = request.form.get('release_date') or None
    if release_date:
        release_date = datetime.strptime(release_date, "%Y-%m-%d").date()

    language = request.form.get('language')
    published_by = get_user_id()

    app_type = request.form.get('app_type')
    category = request.form.get('category')

    comments_allowed = True if request.form.get('comments_allowed') == 'on' else False

    # if errors:
    #     return jsonify(success=False, errors={"link": "Ссылка уже используется"})

    game = db.post_game(
        title, link, comments_allowed, preview, 
        # GameInfo
        description, price, release_date, language, published_by, app_type, category,
        # GameDownload
        game_file
        )
    
    titles = request.form.getlist("download_titles[]")
    files = request.files.getlist("download_files[]")

    for i in range(len(titles)):
        file = files[i]
        new_file = upload_file(file)
        db.add_game_download(game.id, titles[i], new_file.path, new_file.size, order=i)
    
    flash("Игра успешно создана")
    return jsonify(
        success=True,    
        message="Игра успешно создана",
        game_url=f"/game/{game.link}"
        )

@app.get("/game/<link>")
def view_game(link):
    game = db.get_app_one(link)

    if game:
        game_download = game.game_downloads
        game_download = getattr(game, "game_downloads", [])
        return render_template("view_game.html", game=game, game_download=game_download)
    else:
        flash("Приложение не найдено")
        return redirect(furl_for('index'))

from flask import send_from_directory

@app.route('/download/<filename>')
def download_file(filename):
    if filename is None:
        return "Файл не найден", 404
    download_name = db.get_download_info(filename)
    resp = send_from_directory('static/uploads', filename, as_attachment=True, download_name=download_name)
    return resp
    
@app.route('/game/delete/<game_link>')
def delete_game(game_link):
    game = db.get_app_one(game_link)
    db.archive_game(game)

    flash("Игра успешно удалена")
    return redirect(furl_for('index'))

@app.route('/game/edit/<game_link>', methods=['GET', 'POST'])
def edit_game(game_link):
    game = db.get_app_one(game_link)

    if request.method == 'POST':
        title = request.form.get('title')

        comments_allowed = True if request.form.get('comments_allowed') == 'on' else False
        description = request.form.get('description')
        price = request.form.get('price')
        link = game_link

        release_date = request.form.get('release_date') or None
        if release_date:
            release_date = datetime.strptime(release_date, "%Y-%m-%d").date()

        language = request.form.get('language')
        published_by = get_user_id()

        image_file = request.files.get('image_file')
        if image_file and image_file.filename:
            preview = upload_image(image_file)
        else:
            preview = game.preview

        game_file = request.files.get('game_file')
        if game_file and game_file.filename:
            game_file = upload_file(game_file)
        else:
            game_file = None

        db.post_game(
            title, link, comments_allowed, preview,
            # GameInfo
            description, price, release_date, language, published_by,
            # GameDownload
            file=game_file
            )

        return redirect(url_for('view_game'))

    return render_template('edit_game.html', game=game)

@app.get('/file/create')
def add_file():
    return render_template('add_file.html')

@app.post('/file/create')
def post_file():
    title = request.form.get('title')
    link = request.form.get('link')

    uploaded_by = get_user_id()

    image_file = request.files.get('image_file')
    preview = upload_image(image_file)

    my_file = request.files.get('download_file')
    download_file = upload_file(my_file)

    db.post_file(
        title, preview, download_file, link, uploaded_by
    )

    flash("Файл успешно выложен")
    return redirect(link)
    
@app.get("/file/<link>")
def view_file(link):
    shared_file = db.get_files_one(link)

    if shared_file:
        return render_template("view_file.html", shared_file=shared_file)
    else:
        return "File not found", 404
    
@app.get('/file/share')
def file_share_get():
    return render_template('share.html')

@app.get('/file/share')
def file_share_post():
    return redirect(url_for('index'))

@app.get('/user/<username>')
def user(username):
    account = db.get_users_one(username)
    games = db.get_app_by_user(username)
    if account is None:
        return f"Юзер не найден"
    
    return render_template('user.html', account=account, games=games)


# Аккаунт

@app.get('/account/me')
def redirect_to_user():
    return redirect(furl_for('user', username=get_user_id()))


@app.get('/account/register')
def register():
    if is_loggined():
        return redirect(furl_for('index'))
    return render_template('new_account.html')

@app.post('/account/register')
def register_post():
    username = request.form.get('username')
    password = request.form.get('password')
    try:
        db.post_register(username, password)
        flash(f'Аккаунт {username} успешно создан')
        token = db.post_login(username, password)
        session['token'] = token
        return redirect(furl_for('index'))
    except ValueError as e:
        error = (str(e), 'error')
        return render_template('new_account.html', error=error, username=username, password=password)


@app.get('/account/login')
def login():
    if is_loggined():
        return(redirect(furl_for('index')))
    return(render_template('login.html'))

@app.post('/account/login')
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    token = db.post_login(username, password)
    session['token'] = token

    return(redirect(f'/user/{username}'))

@app.route('/account/logout', methods=['POST', 'GET'])
def logout():
    if is_loggined():
        print('успешно удалил токен')
        session.pop('token', None)
    return redirect(furl_for('login'))



if __name__ == "__main__":
    with app.app_context():
        create_tables()

    app.run(debug=True, port=5200, host='0.0.0.0')