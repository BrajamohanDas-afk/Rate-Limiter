from functools import wraps
from flask import request, jsonify
from app.models import Client


def require_api_key(f):
    """
    Decorator that extracts and validates the API key from the X-API-Key header.
    Injects the resolved `client` object into the wrapped function.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get("X-API-Key", "").strip()

        if not api_key:
            return jsonify({"error": "Missing X-API-Key header"}), 401

        client = Client.query.filter_by(api_key=api_key, is_active=True).first()
        if not client:
            return jsonify({"error": "Invalid or inactive API key"}), 401

        return f(*args, client=client, **kwargs)

    return decorated
