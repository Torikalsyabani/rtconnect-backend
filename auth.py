"""
RTConnect - Auth helpers (JWT)
"""
import jwt
import hashlib
import os
import time
from functools import wraps
from flask import request, jsonify, g


def _secret():
    return os.environ.get("SECRET_KEY", "rtconnect_secret_maleber_RT01_2024_key32!")


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_token(user_id: int, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400 * 7,
    }
    return jwt.encode(payload, _secret(), algorithm="HS256")


def decode_token(token: str):
    return jwt.decode(token, _secret(), algorithms=["HS256"], options={"verify_sub": False})


def _extract_user():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None, jsonify({"error": "Token diperlukan"}), 401
    token = auth.split(" ", 1)[1]
    try:
        payload = decode_token(token)
        return payload, None, None
    except jwt.ExpiredSignatureError:
        return None, jsonify({"error": "Token kadaluarsa"}), 401
    except jwt.InvalidTokenError:
        return None, jsonify({"error": "Token tidak valid"}), 401


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        payload, err, code = _extract_user()
        if err:
            return err, code
        g.user_id = payload["sub"]
        g.role    = payload["role"]
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        payload, err, code = _extract_user()
        if err:
            return err, code
        g.user_id = payload["sub"]
        g.role    = payload["role"]
        if g.role != "admin":
            return jsonify({"error": "Hanya admin yang diizinkan"}), 403
        return f(*args, **kwargs)
    return decorated
