from .all_filters import filesize, game_or_app, time_ago

def init_filters(app):
    app.add_template_filter(time_ago, name='time_ago')
    app.add_template_filter(filesize, name='filesize')
    app.add_template_filter(game_or_app, name='game_or_app')
