import secrets
from flask import Blueprint, jsonify, request
from app import db
from app.models import Client, RateLimitConfig

clients_bp = Blueprint("clients", __name__)

VALID_TIERS = {"free", "standard", "premium"}
TIER_DEFAULTS = {
    "free":     {"requests_per_window": 20,  "window_seconds": 60},
    "standard": {"requests_per_window": 60,  "window_seconds": 60},
    "premium":  {"requests_per_window": 200, "window_seconds": 60},
}


@clients_bp.route("", methods=["GET"])
def list_clients():
    clients = Client.query.order_by(Client.created_at.desc()).all()
    return jsonify([c.to_dict() for c in clients]), 200


@clients_bp.route("", methods=["POST"])
def create_client():
    data = request.get_json(silent=True)
    if data is None:
        data = {}
    if not isinstance(data, dict):
        return jsonify({"error": "JSON body must be an object"}), 422

    name = (data.get("name") or "").strip()
    tier = (data.get("tier") or "standard").strip().lower()

    if not name:
        return jsonify({"error": "name is required"}), 422
    if tier not in VALID_TIERS:
        return jsonify({"error": f"tier must be one of {sorted(VALID_TIERS)}"}), 422
    if Client.query.filter_by(name=name).first():
        return jsonify({"error": "A client with this name already exists"}), 409

    api_key = secrets.token_urlsafe(32)
    client = Client(name=name, api_key=api_key, tier=tier)
    db.session.add(client)
    db.session.flush()  # get client.id before committing

    defaults = TIER_DEFAULTS[tier]
    requests_per_window, error = _parse_positive_int(
        data.get("requests_per_window", defaults["requests_per_window"]),
        "requests_per_window",
    )
    if error:
        db.session.rollback()
        return jsonify({"error": error}), 422

    window_seconds, error = _parse_positive_int(
        data.get("window_seconds", defaults["window_seconds"]),
        "window_seconds",
    )
    if error:
        db.session.rollback()
        return jsonify({"error": error}), 422

    config = RateLimitConfig(
        client_id=client.id,
        requests_per_window=requests_per_window,
        window_seconds=window_seconds,
    )
    db.session.add(config)
    db.session.commit()

    return jsonify(client.to_dict()), 201


@clients_bp.route("/<int:client_id>", methods=["GET"])
def get_client(client_id: int):
    client = db.session.get(Client, client_id)
    if client is None:
        return jsonify({"error": "Client not found"}), 404
    return jsonify(client.to_dict()), 200


@clients_bp.route("/<int:client_id>", methods=["PATCH"])
def update_client(client_id: int):
    client = db.session.get(Client, client_id)
    if client is None:
        return jsonify({"error": "Client not found"}), 404
    data = request.get_json(silent=True)
    if data is None:
        data = {}
    if not isinstance(data, dict):
        return jsonify({"error": "JSON body must be an object"}), 422

    if "is_active" in data:
        is_active = data["is_active"]
        if not isinstance(is_active, bool):
            return jsonify({"error": "is_active must be a boolean"}), 422
        client.is_active = is_active

    if "requests_per_window" in data or "window_seconds" in data:
        if data.get("requests_per_window") is not None:
            rpw, error = _parse_positive_int(
                data.get("requests_per_window"),
                "requests_per_window",
            )
            if error:
                return jsonify({"error": error}), 422
            client.rate_config.requests_per_window = rpw

        if data.get("window_seconds") is not None:
            ws, error = _parse_positive_int(
                data.get("window_seconds"),
                "window_seconds",
            )
            if error:
                return jsonify({"error": error}), 422
            client.rate_config.window_seconds = ws

    db.session.commit()
    return jsonify(client.to_dict()), 200


@clients_bp.route("/<int:client_id>", methods=["DELETE"])
def delete_client(client_id: int):
    client = db.session.get(Client, client_id)
    if client is None:
        return jsonify({"error": "Client not found"}), 404
    db.session.delete(client)
    db.session.commit()
    return "", 204


def _parse_positive_int(value, field_name: str) -> tuple[int | None, str | None]:
    if not isinstance(value, int) or value < 1:
        return None, f"{field_name} must be a positive integer"
    return value, None
