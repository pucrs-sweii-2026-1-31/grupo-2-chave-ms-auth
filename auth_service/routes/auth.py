from flask import request, jsonify
from . import auth
from ..services.auth_service import AuthService

auth_service = AuthService()


@auth.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json() or {}
        access_token, refresh_token = auth_service.login(data)
        return jsonify({"access_token": access_token, "refresh_token": refresh_token}), 200
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@auth.route("/refresh", methods=["POST"])
def refresh():
    try:
        data = request.get_json() or {}
        access_token = auth_service.refresh(data)
        return jsonify({"access_token": access_token}), 200
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@auth.route("/logout", methods=["POST"])
def logout():
    try:
        data = request.get_json() or {}
        auth_service.logout(data)
        return jsonify({"message": "Logged out"}), 200
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


@auth.route("/me", methods=["GET"])
def me():
    try:
        user = auth_service.get_current_user(request)
        return jsonify({"user": user}), 200
    except ValueError as error:
        return jsonify({"error": str(error)}), 401
