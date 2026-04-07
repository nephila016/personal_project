"""Tests for web dashboard routes: page loads, auth enforcement, CRUD operations."""
import pytest

from app.database import db
from app.models.admin import Admin
from app.models.order import Order, OrderStatus


class TestDashboardIndex:
    def test_dashboard_loads(self, logged_in_client):
        resp = logged_in_client.get("/dashboard/")
        assert resp.status_code == 200
        assert b"dashboard" in resp.data.lower() or b"Dashboard" in resp.data

    def test_dashboard_requires_auth(self, client):
        resp = client.get("/dashboard/", follow_redirects=False)
        assert resp.status_code == 302


class TestOrderPages:
    def test_orders_page(self, logged_in_client, pending_order):
        resp = logged_in_client.get("/dashboard/orders")
        assert resp.status_code == 200

    def test_orders_page_with_filters(self, logged_in_client, pending_order):
        resp = logged_in_client.get("/dashboard/orders?status=pending&search=John")
        assert resp.status_code == 200

    def test_order_detail_page(self, logged_in_client, pending_order):
        resp = logged_in_client.get(f"/dashboard/orders/{pending_order.id}")
        assert resp.status_code == 200

    def test_order_detail_not_found(self, logged_in_client):
        resp = logged_in_client.get("/dashboard/orders/99999", follow_redirects=True)
        assert resp.status_code == 200
        assert b"not found" in resp.data.lower()

    def test_cancel_order_from_dashboard(self, logged_in_client, pending_order):
        resp = logged_in_client.post(
            f"/dashboard/orders/{pending_order.id}/update-status",
            data={"status": "canceled", "note": "Test"},
            follow_redirects=True,
        )
        assert resp.status_code == 200

    def test_reassign_order_from_dashboard(self, logged_in_client, in_progress_order):
        resp = logged_in_client.post(
            f"/dashboard/orders/{in_progress_order.id}/update-status",
            data={"status": "pending"},
            follow_redirects=True,
        )
        assert resp.status_code == 200

    def test_invalid_status_transition(self, logged_in_client, pending_order):
        resp = logged_in_client.post(
            f"/dashboard/orders/{pending_order.id}/update-status",
            data={"status": "delivered"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Invalid" in resp.data or b"invalid" in resp.data


class TestCustomerPages:
    def test_customers_page(self, logged_in_client, customer):
        resp = logged_in_client.get("/dashboard/customers")
        assert resp.status_code == 200

    def test_customer_detail_page(self, logged_in_client, customer):
        resp = logged_in_client.get(f"/dashboard/customers/{customer.id}")
        assert resp.status_code == 200

    def test_customer_detail_not_found(self, logged_in_client):
        resp = logged_in_client.get("/dashboard/customers/99999", follow_redirects=True)
        assert resp.status_code == 200

    def test_toggle_customer(self, logged_in_client, customer):
        resp = logged_in_client.post(
            f"/dashboard/customers/{customer.id}/toggle",
            follow_redirects=True,
        )
        assert resp.status_code == 200


class TestAdminPages:
    def test_admins_page(self, logged_in_client, admin):
        resp = logged_in_client.get("/dashboard/admins")
        assert resp.status_code == 200

    def test_admin_new_page(self, logged_in_client):
        resp = logged_in_client.get("/dashboard/admins/new")
        assert resp.status_code == 200

    def test_create_admin(self, logged_in_client):
        resp = logged_in_client.post(
            "/dashboard/admins/new",
            data={
                "telegram_id": "555555",
                "full_name": "New Test Admin",
                "phone": "+7777777777",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200

    def test_create_admin_missing_fields(self, logged_in_client):
        resp = logged_in_client.post(
            "/dashboard/admins/new",
            data={"telegram_id": "", "full_name": ""},
            follow_redirects=True,
        )
        assert resp.status_code == 200

    def test_admin_detail_page(self, logged_in_client, admin):
        resp = logged_in_client.get(f"/dashboard/admins/{admin.id}")
        assert resp.status_code == 200

    def test_toggle_admin(self, logged_in_client, admin):
        resp = logged_in_client.post(
            f"/dashboard/admins/{admin.id}/toggle",
            follow_redirects=True,
        )
        assert resp.status_code == 200

    def test_toggle_admin_with_active_orders_blocked(
        self, app, logged_in_client, admin, customer
    ):
        with app.app_context():
            o = Order(
                customer_id=customer.id,
                admin_id=admin.id,
                bottle_count=5,
                delivery_address="test",
                status=OrderStatus.IN_PROGRESS.value,
            )
            db.session.add(o)
            db.session.commit()

        resp = logged_in_client.post(
            f"/dashboard/admins/{admin.id}/toggle",
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Cannot deactivate" in resp.data or b"active orders" in resp.data.lower()


class TestInventoryPage:
    def test_inventory_page(self, logged_in_client, receipt):
        resp = logged_in_client.get("/dashboard/inventory")
        assert resp.status_code == 200
