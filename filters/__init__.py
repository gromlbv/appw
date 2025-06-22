from .all_filters import time_ago, filesize, filesize_nospan, game_or_app

def init_filters(app):
    app.add_template_filter(time_ago, name='time_ago')
    app.add_template_filter(filesize, name='filesize')
    app.add_template_filter(filesize_nospan, name='filesize_nospan')
    app.add_template_filter(game_or_app, name='game_or_app')
