"""Tests for REST API endpoints: orders, customers, admins, inventory, stats."""
import json

import pytest

from app.database import db
from app.models.admin import Admin
from app.models.bottle_receipt import BottleReceipt
from app.models.bottle_return import BottleReturn
from app.models.customer import Customer
from app.models.order import Order, OrderStatus


class TestStatsAPI:
    def test_get_stats(self, logged_in_client, customer, admin, pending_order, receipt):
        resp = logged_in_client.get("/api/v1/stats")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "total_orders" in data
        assert "bottles" in data
        assert data["total_orders"] >= 1
        assert data["pending_orders"] >= 1


class TestOrdersAPI:
    def test_list_orders(self, logged_in_client, pending_order):
        resp = logged_in_client.get("/api/v1/orders")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "items" in data
        assert data["total"] >= 1
        assert "page" in data
        assert "pages" in data

    def test_list_orders_filter_status(self, logged_in_client, pending_order, delivered_order):
        resp = logged_in_client.get("/api/v1/orders?status=pending")
        data = resp.get_json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "pending"

    def test_list_orders_filter_customer(self, logged_in_client, pending_order, customer):
        resp = logged_in_client.get(f"/api/v1/orders?customer_id={customer.id}")
        data = resp.get_json()
        assert data["total"] >= 1

    def test_list_orders_pagination(self, logged_in_client, pending_order):
        resp = logged_in_client.get("/api/v1/orders?page=1&per_page=1")
        data = resp.get_json()
        assert data["per_page"] == 1

    def test_list_orders_sort(self, logged_in_client, pending_order):
        resp = logged_in_client.get("/api/v1/orders?sort=created_at&order=asc")
        assert resp.status_code == 200

    def test_get_order(self, logged_in_client, pending_order):
        resp = logged_in_client.get(f"/api/v1/orders/{pending_order.id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["id"] == pending_order.id
        assert data["bottle_count"] == 5
        assert data["customer"] is not None

    def test_get_order_not_found(self, logged_in_client):
        resp = logged_in_client.get("/api/v1/orders/99999")
        assert resp.status_code == 404

    def test_cancel_order(self, logged_in_client, pending_order):
        resp = logged_in_client.patch(
            f"/api/v1/orders/{pending_order.id}/status",
            data=json.dumps({"status": "canceled", "version": 1, "note": "Test cancel"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "canceled"

    def test_reassign_order(self, logged_in_client, in_progress_order):
        resp = logged_in_client.patch(
            f"/api/v1/orders/{in_progress_order.id}/status",
            data=json.dumps({"status": "pending", "version": 1}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "pending"

    def test_update_status_invalid_transition(self, logged_in_client, pending_order):
        resp = logged_in_client.patch(
            f"/api/v1/orders/{pending_order.id}/status",
            data=json.dumps({"status": "delivered", "version": 1}),
            content_type="application/json",
        )
        assert resp.status_code == 422

    def test_update_status_version_conflict(self, logged_in_client, pending_order):
        resp = logged_in_client.patch(
            f"/api/v1/orders/{pending_order.id}/status",
            data=json.dumps({"status": "canceled", "version": 999}),
            content_type="application/json",
        )
        assert resp.status_code == 409

    def test_update_status_missing_fields(self, logged_in_client, pending_order):
        resp = logged_in_client.patch(
            f"/api/v1/orders/{pending_order.id}/status",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_order_history(self, logged_in_client, pending_order):
        resp = logged_in_client.get(f"/api/v1/orders/{pending_order.id}/history")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "history" in data
        assert data["order_id"] == pending_order.id

    def test_export_orders(self, logged_in_client, pending_order):
        resp = logged_in_client.get("/api/v1/orders/export")
        assert resp.status_code == 200
        assert resp.content_type == "text/csv; charset=utf-8"
        assert b"ID" in resp.data
        assert b"Customer" in resp.data


class TestCustomersAPI:
    def test_list_customers(self, logged_in_client, customer):
        resp = logged_in_client.get("/api/v1/customers")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1
        assert "bottles_in_hand" in data["items"][0]

    def test_list_customers_search(self, logged_in_client, customer):
        resp = logged_in_client.get(f"/api/v1/customers?search=John")
        data = resp.get_json()
        assert data["total"] == 1

    def test_list_customers_is_active_filter(self, logged_in_client, customer):
        resp = logged_in_client.get("/api/v1/customers?is_active=true")
        data = resp.get_json()
        assert data["total"] >= 1

    def test_get_customer(self, logged_in_client, customer):
        resp = logged_in_client.get(f"/api/v1/customers/{customer.id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["full_name"] == "John Doe"
        assert "bottle_stats" in data

    def test_get_customer_not_found(self, logged_in_client):
        resp = logged_in_client.get("/api/v1/customers/99999")
        assert resp.status_code == 404

    def test_update_customer(self, logged_in_client, customer):
        resp = logged_in_client.patch(
            f"/api/v1/customers/{customer.id}",
            data=json.dumps({"full_name": "Updated Name"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["full_name"] == "Updated Name"

    def test_update_customer_toggle_active(self, logged_in_client, customer):
        resp = logged_in_client.patch(
            f"/api/v1/customers/{customer.id}",
            data=json.dumps({"is_active": False}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json()["is_active"] is False

    def test_update_customer_not_found(self, logged_in_client):
        resp = logged_in_client.patch(
            "/api/v1/customers/99999",
            data=json.dumps({"full_name": "X"}),
            content_type="application/json",
        )
        assert resp.status_code == 404

    def test_update_customer_no_valid_fields(self, logged_in_client, customer):
        resp = logged_in_client.patch(
            f"/api/v1/customers/{customer.id}",
            data=json.dumps({"nonexistent": "value"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_customer_bottles(self, logged_in_client, customer):
        resp = logged_in_client.get(f"/api/v1/customers/{customer.id}/bottles")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "bottles_in_hand" in data

    def test_customer_orders(self, logged_in_client, customer, pending_order):
        resp = logged_in_client.get(f"/api/v1/customers/{customer.id}/orders")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1

    def test_export_customers(self, logged_in_client, customer):
        resp = logged_in_client.get("/api/v1/customers/export")
        assert resp.status_code == 200
        assert resp.content_type == "text/csv; charset=utf-8"


class TestAdminsAPI:
    def test_list_admins(self, logged_in_client, admin):
        resp = logged_in_client.get("/api/v1/admins")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1

    def test_create_admin(self, logged_in_client):
        resp = logged_in_client.post(
            "/api/v1/admins",
            data=json.dumps({
                "telegram_id": 333333,
                "full_name": "New Admin",
                "phone": "+5555555555",
            }),
            content_type="application/json",
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["full_name"] == "New Admin"

    def test_create_admin_duplicate(self, logged_in_client, admin):
        resp = logged_in_client.post(
            "/api/v1/admins",
            data=json.dumps({
                "telegram_id": admin.telegram_id,
                "full_name": "Dup Admin",
            }),
            content_type="application/json",
        )
        assert resp.status_code == 409

    def test_create_admin_missing_fields(self, logged_in_client):
        resp = logged_in_client.post(
            "/api/v1/admins",
            data=json.dumps({"telegram_id": 444444}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    def test_get_admin(self, logged_in_client, admin):
        resp = logged_in_client.get(f"/api/v1/admins/{admin.id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["full_name"] == "Bot Admin"
        assert "inventory" in data

    def test_get_admin_not_found(self, logged_in_client):
        resp = logged_in_client.get("/api/v1/admins/99999")
        assert resp.status_code == 404

    def test_update_admin(self, logged_in_client, admin):
        resp = logged_in_client.patch(
            f"/api/v1/admins/{admin.id}",
            data=json.dumps({"full_name": "Updated Admin"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["full_name"] == "Updated Admin"

    def test_update_admin_not_found(self, logged_in_client):
        resp = logged_in_client.patch(
            "/api/v1/admins/99999",
            data=json.dumps({"full_name": "X"}),
            content_type="application/json",
        )
        assert resp.status_code == 404

    def test_admin_stock(self, logged_in_client, admin, receipt):
        resp = logged_in_client.get(f"/api/v1/admins/{admin.id}/stock")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["current_stock"] == 50

    def test_deactivate_admin(self, logged_in_client, admin):
        resp = logged_in_client.delete(f"/api/v1/admins/{admin.id}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["is_active"] is False

    def test_deactivate_admin_with_active_orders(self, logged_in_client, admin, in_progress_order):
        resp = logged_in_client.delete(f"/api/v1/admins/{admin.id}")
        assert resp.status_code == 422


class TestInventoryAPI:
    def test_overview(self, logged_in_client, receipt):
        resp = logged_in_client.get("/api/v1/inventory/overview")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "total_received" in data

    def test_receipts(self, logged_in_client, receipt):
        resp = logged_in_client.get("/api/v1/inventory/receipts")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1

    def test_receipts_filter_admin(self, logged_in_client, admin, receipt):
        resp = logged_in_client.get(f"/api/v1/inventory/receipts?admin_id={admin.id}")
        data = resp.get_json()
        assert data["total"] >= 1

    def test_returns(self, app, logged_in_client, customer, admin, receipt):
        with app.app_context():
            o = Order(
                customer_id=customer.id,
                admin_id=admin.id,
                bottle_count=10,
                delivery_address="test",
                status=OrderStatus.DELIVERED.value,
            )
            db.session.add(o)
            db.session.commit()
            br = BottleReturn(
                customer_id=customer.id,
                admin_id=admin.id,
                quantity=3,
            )
            db.session.add(br)
            db.session.commit()

        resp = logged_in_client.get("/api/v1/inventory/returns")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total"] >= 1

    def test_export_inventory(self, logged_in_client, receipt):
        resp = logged_in_client.get("/api/v1/inventory/export")
        assert resp.status_code == 200
        assert resp.content_type == "text/csv; charset=utf-8"
        assert b"Receipts" in resp.data
