from hashlib import sha256
import jwt

from datetime import datetime, timedelta
import time

secretkey = 'rulevsecretkey'


def myhash(message):
    message = message.encode()
    message = sha256(message)
    message = message.hexdigest()
    return message


def encode(user_id):
    iat = int(time.time())
    exp = int((datetime.now() + timedelta(weeks=2)).timestamp())
    encoded_jwt = jwt.encode(
        {
            'sub': user_id,
            'iat': iat,
            'exp': exp
        },
        secretkey,
        algorithm="HS256"
    )
    return encoded_jwt


def decode(token):
    try:
        payload = jwt.decode(
            token,
            secretkey,
            algorithms=["HS256"]
        )
        return payload['sub']
    except jwt.ExpiredSignatureError:
        print("Токен истёк")
    except jwt.InvalidTokenError:
        print("Недействительный токен")

    return None


def verify(token):
    try:
        jwt.decode(
            token,
            secretkey,
            algorithms=["HS256"]
        )
    
    except jwt.ExpiredSignatureError:
        return False
    
    except jwt.InvalidTokenError:
        return False
    
    return token