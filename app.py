from flask import Flask
from flask import render_template, session, request, flash, redirect, jsonify, url_for

from models import create_app, create_tables
from mysecurity import verify, decode
from upload import upload_image, upload_file, upload_unity_build
from functools import wraps

import mydb as db
from datetime import datetime
from rapidfuzz import process, fuzz
import re

import redis
from functools import wraps
from utils import json_response



app = Flask(__name__)
create_app(app)

app.secret_key = 'rulevsecretkey'
app.config['SERVER_NAME'] = "appw.su"

r = redis.Redis()

def handle_valueerror_htmx():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ValueError as e:
                return str(e), 400
        return wrapper
    return decorator

def rate_limit(timeout=1, max_attempts=5):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_ip = request.remote_addr
            if not user_ip:
                return json_response({
                    'type': 'error',
                    'message': 'Что-то пошло не так <a href="https://lbv_dev.t.me">Поддержка</a>'
                })

            counter_key = f"rl_counter:{user_ip}"

            attempts = r.incr(counter_key)
            if attempts == 1:
                r.expire(counter_key, timeout)
            if attempts > max_attempts:
                return json_response({
                    'type': 'warning',
                    'message': 'Слишком быстро кликаешь!'
                })
            if attempts > 20:
                return json_response({
                    'type': 'warning',
                    'message': 'Чего?'
                })
            if attempts > 100:
                return json_response({
                    'type': 'warning',
                    'message': 'Окей на этом моменте виноват точно я'
                })
            
            if r.exists(user_ip):
                return json_response({
                    'type': 'warning',
                    'message': 'Подождите 1 секунду перед повторной отправкой'
                })

            r.setex(user_ip, timeout, "blocked")
            return f(*args, **kwargs)
        return wrapper
    return decorator

def handle_valueerror(template_name):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except ValueError as e:
                context = dict(request.form)
                context['error'] = str(e)
                return render_template(template_name, **context)
        return wrapped
    return decorator

from datetime import datetime, timedelta
import pytz
from flask import g, request

@app.template_filter('time_ago')
def time_ago_filter(dt):
    if not dt:
        return "никогда"
    
    user_tz = getattr(g, 'user_timezone', None) or request.cookies.get('timezone') or 'UTC'
    
    try:
        tz = pytz.timezone(user_tz)
        now = datetime.now(tz)
        local_dt = dt.replace(tzinfo=pytz.utc).astimezone(tz)
        
        diff = now - local_dt
    except:
        now = datetime.now()
        diff = now - dt

    if diff < timedelta(minutes=1):
        return "только что"
    elif diff < timedelta(hours=1):
        minutes = int(diff.seconds / 60)
        return f"{minutes} {pluralize(minutes, 'минуту', 'минуты', 'минут')} назад"
    elif diff < timedelta(days=1):
        hours = int(diff.seconds / 3600)
        return f"{hours} {pluralize(hours, 'час', 'часа', 'часов')} назад"
    elif diff < timedelta(days=2):
        return "вчера"
    elif diff < timedelta(days=7):
        return f"{diff.days} {pluralize(diff.days, 'день', 'дня', 'дней')} назад"
    elif dt.year == now.year:
        return dt.strftime("%d %b")
    else:
        return dt.strftime("%d %b %Y")

def pluralize(n, form1, form2, form5):
    n = abs(n) % 100
    n1 = n % 10
    if 10 < n < 20:
        return form5
    if 1 < n1 < 5:
        return form2
    if n1 == 1:
        return form1
    return form5

@app.template_filter('filesize')
def filesize_filter(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f} <span>{unit}</span>"
        size /= 1024
    return f"{size:.1f} PB"

# возвращает "игры" или "приложения" в зависимости от типа
@app.template_filter('game_or_app')
def game_or_app(app_type):
    return 'game' if app_type == 'игры' else 'приложения'



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

def compare_users(username):
    current_user = get_user_id()
    if current_user == 'lbv': # обход для меня 
        return True
    if not current_user:
        return False
    return current_user == username

@app.route('/form')
def form():
    return render_template('form.html')



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


@app.get('/add')
def add_game():
    if not is_loggined():
        flash("Чтобы добавить игру необходимо <a href='/account/login'>Войти в аккаунт</a>")
        return redirect(url_for('index'))
    return render_template('add_game.html')


@app.post('/add')
@rate_limit(timeout=1)
def post_game():
    if not is_loggined():
        flash("Чтобы добавить игру необходимо <a href='/account/login'>Войти в аккаунт</a>")
        return redirect(url_for('index'))
    
    title = request.form.get('title')
    link = request.form.get('link')

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

    is_unity_build = True if request.form.get('is_unity_build') == 'on' else False

    try:
        game = db.post_game(
            title, link, comments_allowed, is_unity_build, preview,
            description, price, release_date, language, published_by, app_type, category,
        )
    except ValueError as e:
        return json_response({
            'type': 'error',
            'message': str(e)
        })

    if is_unity_build:
        file = request.files.get('unity_file')
        if not file:
            db.delete_game(game.id)
            return json_response({
                'type': 'error',
                'message': "Не нашел файла Unity сборки (.zip)"
            })
        
        try:
            new_file = upload_unity_build(file, game.id)
            if not new_file:
                return json_response({
                    'type': 'error',
                    'message': "Ошибка загрузки Unity сборки"
                })
            
            db.add_game_download(game.id, "unity_build", new_file.path, new_file.size, order=0)
        except ValueError as e:
            db.delete_game(game.id)
            return json_response({
                'type': 'error',
                'message': str(e)
            })
    else:
        titles = request.form.getlist("download_titles[]")
        files = request.files.getlist("download_files[]")

        for i in range(len(titles)):
            file = files[i] if i < len(files) else None
            if file:
                new_file = upload_file(file)
                if new_file:    
                    db.add_game_download(game.id, titles[i], new_file.path, new_file.size, order=i)
                    
    flash(f"Приложение успешно добавлено! <a href='/a/{link}'>Открыть</a>")
    return json_response({
        'type': 'success',  
        'redirect_to': url_for('index')
    })



@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return ''

    all_results = db.get_shares_all()

    direct_matches = [
        r for r in all_results
        if query.lower() in r.title.lower()
    ]

    results = direct_matches

    if len(results) < 10:
        titles = [r.title for r in all_results]
        fuzzy_matches = process.extract(query, titles, scorer=fuzz.token_set_ratio, limit=10)
        fuzzy_titles = {m[0] for m in fuzzy_matches if m[1] > 60}

        fuzz_results = [
            r for r in all_results
            if r.title in fuzzy_titles and r not in results
        ]
        results += fuzz_results

    if not results:
        return '<p>Ничего не найдено</p>'

    def highlight(text, query):
        pattern = re.escape(query)
        return re.sub(f"({pattern})", r"<mark>\1</mark>", text, flags=re.IGNORECASE)

    html = ''.join(
        f'<a class="suggestion-item" href="/a/{r.link}">{highlight(r.title, query)}</a>'
        for r in results
    )

    return html



@app.route('/', subdomain="<game_link>")
def view_game_subdomain(game_link):
    flash("СУБДОМЕН НА", game_link)
    game = db.get_app_one(game_link)
    if game:
        game_download = getattr(game, "downloads", [])
        return render_template("view_game.html", game=game, game_download=game_download)
    else:
        flash("Приложение не найдено")
        return redirect(url_for("index"))
    

@app.get("/a/<link>")
def view_game(link):
    game = db.get_app_one(link)

    if game:
        game_download = game.downloads
        game_download = getattr(game, "downloads", [])
        return render_template("view_game.html", game=game, game_download=game_download)
    else:
        flash("Приложение не найдено")
        return redirect(url_for('index'))

from flask import send_from_directory

@app.route('/download/<filename>')
def download_file(filename):
    if filename is None:
        return "Файл не найден", 404
    download_name = db.get_download_info(filename)
    resp = send_from_directory('static/uploads', filename, as_attachment=True, download_name=download_name)
    return resp
    
@app.route('/hide/<game_link>')
def delete_game(game_link):
    game = db.get_app_one(game_link)
    if not game:
        flash("Игра не найдена")
        return redirect(url_for('index'))

    if not compare_users(game.info.published_by):
        flash("Вы не можете удалить чужую игру")
        return redirect(url_for('view_game', link=game_link))

    db.archive_game(game)
    flash("Игра успешно скрыта")
    return redirect(url_for('index'))



@app.route('/api/a/<link>/modal')
def game_modal(link):
    game = db.get_app_one(link)
    if not game:
        return "Игра не найдена", 404
    is_admin = compare_users(game.info.published_by)
    
    return render_template('game_modal.html', game=game, is_admin=is_admin)

@app.route('/edit/<game_link>', methods=['GET', 'POST'])
def edit_game(game_link):
    game = db.get_app_one(game_link)

    if not game:
        return "Игра не найдена", 404

    if request.method == 'POST':
        title = request.form.get('title')
        comments_allowed = request.form.get('comments_allowed') == 'on'
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

        db.post_game_edit(
            game.id, title, link, comments_allowed, game.is_unity_build, preview,
            description, price, release_date, language, published_by,
            game.info.app_type, game.info.category
        )

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
    return redirect(url_for('view_file', link=link))
    
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
    
    is_guest = compare_users(username)

    return render_template('user.html', account=account, games=games, is_guest=is_guest)



# Аккаунт

@app.get('/account/me')
def redirect_to_user():
    return redirect(url_for('user', username=get_user_id()))


@app.get('/account/register')
def register():
    if is_loggined():
        return redirect(url_for('index'))
    return render_template('new_account.html')

@app.route('/account/register', methods=['POST'])
@handle_valueerror('new_account.html')
def register_post():
    username = request.form.get('username')
    password = request.form.get('password')
    db.post_register(username, password)
    flash(f'Аккаунт {username} успешно создан')
    token = db.post_login(username, password)
    session['token'] = token
    return redirect(url_for('index'))

@app.get('/account/login')
def login():
    if is_loggined():
        return(redirect(url_for('index')))
    return(render_template('login.html'))

@app.post('/account/login')
@handle_valueerror('login.html')
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    token = db.post_login(username, password)
    session['token'] = token

    return(redirect(f'/user/{username}'))

@app.route('/api/a/<game_link>')
def api_game(game_link):
    game = db.get_app_one(game_link)
    if not game:
        return {"error": "Игра не найдена"}, 404
    data = {
        "title": game.title,
        "preview": game.preview,
        "description": game.info.description or "Описание отсутствует",
        "downloads": [
            {"title": d.title or "Без названия", "file_link": url_for('download_file', filename=d.file_link)}
            for d in getattr(game, "downloads", [])
        ],
        "release_date": game.info.release_date or "Дата релиза не указана",
        "language": game.info.language or "Язык не указан",
        "author": game.info.published_by,
        "price": game.info.price,
        "app_type": game.info.app_type,
        "category": game.info.category,
        "link": game.link,

        "is_admin": compare_users(game.uploaded_by),
    }
    print(data['is_admin'])
    return data

@app.route('/account/logout', methods=['POST', 'GET'])
def logout():
    if is_loggined():
        session.pop('token', None)
        flash("Вы вышли из аккаунта <a href='/account/login'>Вход</a>")

    return redirect(url_for('index'))





@app.get('/graphs')
def graphs():
    games = db.get_shares_all()

    apps = []
    for game in games:
        size = game.downloads[0].file_size if game.downloads else 0
        apps.append({
            'link': game.link,
            'title': game.title,
            'size': size,
                'game_stats': {
                    'serious_fun': game.stats.serious_fun if game.stats else 50,
                    'utility_gamified': game.stats.utility_gamified if game.stats else 50,
                }
        })

    return render_template(
        "graphs.html",
        users=db.get_users_all(),
        apps=apps,
        games=games,
    )

@app.route('/graphs/edit', methods=['GET', 'POST'])
def graphs_edit():
    if request.method == 'POST':
        for key in request.form:
            if key.startswith('serious_fun_'):
                game_id = int(key.split('_')[-1])
                serious_fun = int(request.form.get(f'serious_fun_{game_id}', 50))
                utility_gamified = int(request.form.get(f'utility_gamified_{game_id}', 50))
                db.update_game_stats(game_id, serious_fun, utility_gamified)
        return redirect(url_for('graphs_edit'))

    games = db.get_all_games_with_stats()
    return render_template('graphs_edit.html', games=games)



if __name__ == "__main__":
    with app.app_context():
        create_tables()
    app.run(debug=True, port=5200, host='0.0.0.0')