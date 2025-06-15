from flask import jsonify

def json_response(type_=None, message=None, icon=None, redirect_to=None):
    return jsonify({
        'type': type_,  # 'error', 'warning', 'info', 'success'
        'message': message,
        'icon': icon,   # пока что нет
        'redirect_to': redirect_to
    })