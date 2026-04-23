"""
Tests for the /api/clients CRUD endpoints.
Verifies input validation, happy paths, and error responses.
"""
import json


class TestCreateClient:
    def test_create_client_success(self, http_client, db):
        resp = http_client.post(
            "/api/clients",
            json={"name": "acme", "tier": "standard"},
            content_type="application/json",
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["name"] == "acme"
        assert body["tier"] == "standard"
        assert "api_key" in body

    def test_create_client_missing_name_returns_422(self, http_client, db):
        resp = http_client.post("/api/clients", json={"tier": "free"})
        assert resp.status_code == 422

    def test_create_client_invalid_tier_returns_422(self, http_client, db):
        resp = http_client.post("/api/clients", json={"name": "x", "tier": "ultra"})
        assert resp.status_code == 422

    def test_duplicate_name_returns_409(self, http_client, db):
        http_client.post("/api/clients", json={"name": "dup"})
        resp = http_client.post("/api/clients", json={"name": "dup"})
        assert resp.status_code == 409

    def test_create_client_invalid_requests_per_window_returns_422(self, http_client, db):
        resp = http_client.post(
            "/api/clients",
            json={"name": "bad-limits", "requests_per_window": 0},
        )
        assert resp.status_code == 422

    def test_create_client_invalid_json_shape_returns_422(self, http_client, db):
        resp = http_client.post(
            "/api/clients",
            data=json.dumps(["not", "an", "object"]),
            content_type="application/json",
        )
        assert resp.status_code == 422


class TestListClients:
    def test_empty_list(self, http_client, db):
        resp = http_client.get("/api/clients")
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_returns_created_clients(self, http_client, db):
        http_client.post("/api/clients", json={"name": "client-a"})
        http_client.post("/api/clients", json={"name": "client-b"})
        resp = http_client.get("/api/clients")
        assert len(resp.get_json()) == 2


class TestUpdateClient:
    def test_deactivate_client(self, http_client, db, client_obj):
        resp = http_client.patch(f"/api/clients/{client_obj.id}", json={"is_active": False})
        assert resp.status_code == 200
        assert resp.get_json()["is_active"] is False

    def test_update_rate_limit(self, http_client, db, client_obj):
        resp = http_client.patch(
            f"/api/clients/{client_obj.id}",
            json={"requests_per_window": 999},
        )
        assert resp.status_code == 200
        assert resp.get_json()["rate_config"]["requests_per_window"] == 999

    def test_invalid_window_returns_422(self, http_client, db, client_obj):
        resp = http_client.patch(
            f"/api/clients/{client_obj.id}",
            json={"window_seconds": -10},
        )
        assert resp.status_code == 422

    def test_invalid_is_active_type_returns_422(self, http_client, db, client_obj):
        resp = http_client.patch(
            f"/api/clients/{client_obj.id}",
            json={"is_active": "false"},
        )
        assert resp.status_code == 422


class TestGateway:
    def test_valid_key_returns_200(self, http_client, db, client_obj):
        resp = http_client.get(
            "/api/gateway/hello",
            headers={"X-API-Key": client_obj.api_key},
        )
        assert resp.status_code == 200
        assert "X-RateLimit-Limit" in resp.headers

    def test_missing_key_returns_401(self, http_client, db):
        resp = http_client.get("/api/gateway/hello")
        assert resp.status_code == 401

    def test_invalid_key_returns_401(self, http_client, db):
        resp = http_client.get("/api/gateway/hello", headers={"X-API-Key": "bad-key"})
        assert resp.status_code == 401

    def test_rate_limit_enforced(self, http_client, db, client_obj):
        limit = client_obj.rate_config.requests_per_window  # 5
        for _ in range(limit):
            http_client.get("/api/gateway/x", headers={"X-API-Key": client_obj.api_key})

        resp = http_client.get("/api/gateway/x", headers={"X-API-Key": client_obj.api_key})
        assert resp.status_code == 429
        assert "Retry-After" in resp.headers


class TestStats:
    def test_timeline_invalid_minutes_returns_422(self, http_client, db):
        resp = http_client.get("/api/stats/timeline?minutes=hello")
        assert resp.status_code == 422

    def test_timeline_minutes_bounds_enforced(self, http_client, db):
        resp = http_client.get("/api/stats/timeline?minutes=0")
        assert resp.status_code == 422
