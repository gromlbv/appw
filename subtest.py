from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def index():
    host = request.host.split(':')[0] 
    if host == 'appw.local':
        return 'Главный домен'
    elif host == 'test.appw.local':
        return 'Субдомен test'
    elif host == 'app.appw.local':
        return 'Субдомен app'
    else:
        return 'Неизвестный домен'

if __name__ == '__main__':
    app.run(debug=True, port=5200)
