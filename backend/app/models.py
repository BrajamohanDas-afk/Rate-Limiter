from datetime import datetime, timezone
from app import db


class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    api_key = db.Column(db.String(64), nullable=False, unique=True, index=True)
    tier = db.Column(db.String(20), nullable=False, default="standard")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    rate_config = db.relationship("RateLimitConfig", back_populates="client", uselist=False, cascade="all, delete-orphan")
    request_logs = db.relationship("RequestLog", back_populates="client", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "api_key": self.api_key,
            "tier": self.tier,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "rate_config": self.rate_config.to_dict() if self.rate_config else None,
        }


class RateLimitConfig(db.Model):
    __tablename__ = "rate_limit_configs"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False, unique=True)
    requests_per_window = db.Column(db.Integer, nullable=False, default=100)
    window_seconds = db.Column(db.Integer, nullable=False, default=60)
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    client = db.relationship("Client", back_populates="rate_config")

    def to_dict(self) -> dict:
        return {
            "requests_per_window": self.requests_per_window,
            "window_seconds": self.window_seconds,
        }


class RequestLog(db.Model):
    __tablename__ = "request_logs"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False, index=True)
    path = db.Column(db.String(255), nullable=False)
    status_code = db.Column(db.Integer, nullable=False)
    was_throttled = db.Column(db.Boolean, nullable=False, default=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    client = db.relationship("Client", back_populates="request_logs")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "client_id": self.client_id,
            "path": self.path,
            "status_code": self.status_code,
            "was_throttled": self.was_throttled,
            "timestamp": self.timestamp.isoformat(),
        }
