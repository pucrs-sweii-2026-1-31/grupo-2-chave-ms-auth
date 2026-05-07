from flask import Blueprint

auth = Blueprint("auth", __name__)

from .auth import *  # noqa: F401, E402
