import pytz
from flask import request, g
from datetime import datetime, timedelta

from tools import pluralize


def filesize(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f} <span>{unit}</span>"
        size /= 1024
    return f"{size:.1f} PB"

def filesize_nospan(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f} PB"

def game_or_app(app_type):
    return 'игры' if app_type == 'игры' else 'приложения'


def time_ago(dt):
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