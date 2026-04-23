from flask import Blueprint, jsonify, request
from app.middleware.auth import require_api_key
from app.services import rate_limiter

gateway_bp = Blueprint("gateway", __name__)


@gateway_bp.route("/<path:subpath>", methods=["GET", "POST", "PUT", "DELETE"])
@require_api_key
def proxy(subpath: str, client):
    """
    Simulated API gateway endpoint. Every request here is rate-limit checked.
    In a real system this would forward to an upstream service.
    """
    result = rate_limiter.check_and_record(client, path=f"/{subpath}")

    headers = {
        "X-RateLimit-Limit": str(result.limit),
        "X-RateLimit-Remaining": str(result.remaining),
    }

    if not result.allowed:
        headers["Retry-After"] = str(result.retry_after)
        return (
            jsonify({
                "error": "Rate limit exceeded",
                "retry_after_seconds": result.retry_after,
            }),
            429,
            headers,
        )

    return (
        jsonify({
            "message": f"Request to /{subpath} accepted",
            "client": client.name,
            "rate_limit": {"limit": result.limit, "remaining": result.remaining},
        }),
        200,
        headers,
    )
