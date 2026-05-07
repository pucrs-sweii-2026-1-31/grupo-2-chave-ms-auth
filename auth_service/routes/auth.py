from flask import Blueprint, jsonify, request

from ..services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__, url_prefix="")


def _get_bearer_token():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]
    return None


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email")
    password = payload.get("password")

    if not email or not password:
        return jsonify({"error": "email e senha são obrigatórios"}), 400

    user = AuthService.authenticate_user(email, password)
    if not user:
        return jsonify({"error": "credenciais inválidas"}), 401

    access_token = AuthService.create_access_token(user)
    refresh_token = AuthService.create_refresh_token(user)
    return jsonify({"access_token": access_token, "refresh_token": refresh_token}), 200


@auth_bp.post("/refresh")
def refresh():
    payload = request.get_json(silent=True) or {}
    refresh_token = payload.get("refresh_token") or _get_bearer_token()

    if not refresh_token:
        return jsonify({"error": "refresh_token é obrigatório"}), 400

    try:
        access_token = AuthService.refresh_access_token(refresh_token)
        return jsonify({"access_token": access_token}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 401


@auth_bp.post("/logout")
def logout():
    token = _get_bearer_token()
    if not token:
        return jsonify({"error": "Authorization Bearer token é obrigatório"}), 400

    AuthService.revoke_token(token)
    return jsonify({"message": "logout realizado"}), 200


@auth_bp.get("/me")
def me():
    token = _get_bearer_token()
    if not token:
        return jsonify({"error": "Authorization Bearer token é obrigatório"}), 400

    try:
        user = AuthService.get_user_from_token(token)
        return jsonify({"user": user.to_dict()}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 401
