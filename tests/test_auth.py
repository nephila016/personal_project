"""Tests for web authentication: login, logout, lockout, password change."""
from datetime import datetime, timedelta, timezone

import pytest

from app.database import db
from app.models.global_admin import GlobalAdmin


class TestLogin:
    def test_login_page_renders(self, client):
        resp = client.get("/login")
        assert resp.status_code == 200
        assert b"Login" in resp.data or b"login" in resp.data

    def test_login_success(self, client, global_admin):
        resp = client.post("/login", data={
            "username": "testadmin",
            "password": "testpass123",
        }, follow_redirects=False)
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers.get("Location", "")

    def test_login_wrong_password(self, client, global_admin):
        resp = client.post("/login", data={
            "username": "testadmin",
            "password": "wrong",
        })
        assert resp.status_code == 200
        assert b"Invalid" in resp.data

    def test_login_nonexistent_user(self, client):
        resp = client.post("/login", data={
            "username": "nobody",
            "password": "pass",
        })
        assert resp.status_code == 200
        assert b"Invalid" in resp.data

    def test_login_increments_failed_attempts(self, app, client, global_admin):
        client.post("/login", data={
            "username": "testadmin",
            "password": "wrong",
        })
        with app.app_context():
            admin = db.session.get(GlobalAdmin, global_admin.id)
            assert admin.failed_login_attempts == 1

    def test_account_lockout_after_max_attempts(self, app, client, session):
        """Create admin with 9 failed attempts, then one more triggers lockout."""
        ga = GlobalAdmin(
            username="lockme",
            full_name="Lock Test",
            must_change_password=False,
            failed_login_attempts=9,
        )
        ga.set_password("secret")
        session.add(ga)
        session.commit()

        resp = client.post("/login", data={
            "username": "lockme",
            "password": "wrong",
        }, follow_redirects=True)
        assert b"locked" in resp.data.lower() or b"Too many" in resp.data

    def test_locked_account_rejected(self, client, session):
        """Create admin that is already locked."""
        ga = GlobalAdmin(
            username="alreadylocked",
            full_name="Already Locked",
            must_change_password=False,
            locked_until=datetime.now(timezone.utc) + timedelta(minutes=30),
        )
        ga.set_password("secret")
        session.add(ga)
        session.commit()

        resp = client.post("/login", data={
            "username": "alreadylocked",
            "password": "secret",
        }, follow_redirects=True)
        assert b"locked" in resp.data.lower()

    def test_successful_login_resets_attempts(self, app, client, session):
        """Create admin with prior failed attempts; successful login resets them."""
        ga = GlobalAdmin(
            username="resetme",
            full_name="Reset Test",
            must_change_password=False,
            failed_login_attempts=5,
        )
        ga.set_password("goodpass")
        session.add(ga)
        session.commit()
        ga_id = ga.id

        client.post("/login", data={
            "username": "resetme",
            "password": "goodpass",
        })
        with app.app_context():
            refreshed = db.session.get(GlobalAdmin, ga_id)
            assert refreshed.failed_login_attempts == 0

    def test_deactivated_account_rejected(self, client, session):
        """Create deactivated admin; login should fail."""
        ga = GlobalAdmin(
            username="deactivated",
            full_name="Deactivated Admin",
            must_change_password=False,
            is_active=False,
        )
        ga.set_password("secret")
        session.add(ga)
        session.commit()

        resp = client.post("/login", data={
            "username": "deactivated",
            "password": "secret",
        }, follow_redirects=True)
        assert b"deactivated" in resp.data.lower()


class TestLogout:
    def test_logout_redirects(self, logged_in_client):
        resp = logged_in_client.get("/logout", follow_redirects=False)
        assert resp.status_code == 302

    def test_logout_clears_session(self, logged_in_client):
        logged_in_client.get("/logout")
        resp = logged_in_client.get("/dashboard/", follow_redirects=False)
        assert resp.status_code == 302  # redirects to login


class TestChangePassword:
    def test_must_change_password_redirect(self, client, session):
        ga = GlobalAdmin(
            username="mustchange",
            full_name="Must Change",
            must_change_password=True,
        )
        ga.set_password("temppass")
        session.add(ga)
        session.commit()

        resp = client.post("/login", data={
            "username": "mustchange",
            "password": "temppass",
        }, follow_redirects=False)
        assert resp.status_code == 302
        assert "change-password" in resp.headers.get("Location", "")

    def test_change_password_success(self, logged_in_client):
        resp = logged_in_client.post("/change-password", data={
            "new_password": "newpass123",
            "confirm_password": "newpass123",
        }, follow_redirects=False)
        assert resp.status_code == 302

    def test_change_password_mismatch(self, logged_in_client):
        resp = logged_in_client.post("/change-password", data={
            "new_password": "newpass123",
            "confirm_password": "different",
        })
        assert resp.status_code == 200


class TestProtectedRoutes:
    def test_dashboard_requires_login(self, client):
        resp = client.get("/dashboard/", follow_redirects=False)
        assert resp.status_code == 302

    def test_api_requires_login(self, client):
        resp = client.get("/api/v1/stats")
        assert resp.status_code == 302 or resp.status_code == 401

    def test_orders_requires_login(self, client):
        resp = client.get("/dashboard/orders", follow_redirects=False)
        assert resp.status_code == 302
