from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request
from sqlalchemy import func
from app import db
from app.models import Client, RequestLog

stats_bp = Blueprint("stats", __name__)


@stats_bp.route("/summary", methods=["GET"])
def summary():
    """Aggregate stats for the dashboard header cards."""
    since = datetime.now(timezone.utc) - timedelta(minutes=60)

    total_requests = (
        db.session.query(func.count(RequestLog.id))
        .filter(RequestLog.timestamp >= since)
        .scalar()
        or 0
    )
    throttled = db.session.query(func.count(RequestLog.id)).filter(
        RequestLog.timestamp >= since,
        RequestLog.was_throttled.is_(True),
    ).scalar() or 0
    active_clients = (
        db.session.query(func.count(Client.id))
        .filter(Client.is_active.is_(True))
        .scalar()
        or 0
    )

    return jsonify({
        "last_60_min": {
            "total_requests": total_requests,
            "throttled_requests": throttled,
            "throttle_rate_pct": round((throttled / total_requests * 100) if total_requests else 0, 1),
        },
        "active_clients": active_clients,
    }), 200


@stats_bp.route("/timeline", methods=["GET"])
def timeline():
    """Request counts bucketed by minute for the last 30 minutes."""
    minutes_value = request.args.get("minutes", "30")
    try:
        minutes = int(minutes_value)
    except (TypeError, ValueError):
        return jsonify({"error": "minutes must be an integer"}), 422
    if minutes < 1 or minutes > 720:
        return jsonify({"error": "minutes must be between 1 and 720"}), 422

    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    logs = (
        db.session.query(RequestLog)
        .filter(RequestLog.timestamp >= since)
        .order_by(RequestLog.timestamp)
        .all()
    )

    # Build minute-level buckets
    buckets: dict[str, dict] = {}
    now = datetime.now(timezone.utc)
    for i in range(minutes):
        t = now - timedelta(minutes=(minutes - 1 - i))
        key = t.strftime("%H:%M")
        buckets[key] = {"time": key, "total": 0, "throttled": 0}

    for log in logs:
        key = log.timestamp.strftime("%H:%M")
        if key in buckets:
            buckets[key]["total"] += 1
            if log.was_throttled:
                buckets[key]["throttled"] += 1

    return jsonify(list(buckets.values())), 200


@stats_bp.route("/clients/<int:client_id>", methods=["GET"])
def client_stats(client_id: int):
    """Per-client stats for the last 60 minutes."""
    client = Client.query.get_or_404(client_id)
    since = datetime.now(timezone.utc) - timedelta(minutes=60)

    logs = (
        RequestLog.query
        .filter(RequestLog.client_id == client_id, RequestLog.timestamp >= since)
        .order_by(RequestLog.timestamp.desc())
        .limit(200)
        .all()
    )

    total = len(logs)
    throttled = sum(1 for l in logs if l.was_throttled)

    return jsonify({
        "client": client.to_dict(),
        "last_60_min": {
            "total_requests": total,
            "throttled_requests": throttled,
        },
        "recent_logs": [l.to_dict() for l in logs[:50]],
    }), 200


@stats_bp.route("/throttled-clients", methods=["GET"])
def throttled_clients():
    """Clients with the most throttled requests in the last hour."""
    since = datetime.now(timezone.utc) - timedelta(minutes=60)

    rows = (
        db.session.query(
            Client.id,
            Client.name,
            Client.tier,
            func.count(RequestLog.id).label("throttled_count"),
        )
        .join(RequestLog, RequestLog.client_id == Client.id)
        .filter(RequestLog.was_throttled.is_(True), RequestLog.timestamp >= since)
        .group_by(Client.id, Client.name, Client.tier)
        .order_by(func.count(RequestLog.id).desc())
        .limit(10)
        .all()
    )

    return jsonify([
        {"id": r.id, "name": r.name, "tier": r.tier, "throttled_count": r.throttled_count}
        for r in rows
    ]), 200
