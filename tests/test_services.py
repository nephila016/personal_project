"""Tests for service layer: order state machine, bottle calculations, customer CRUD."""
import pytest

from app.database import db
from app.models.bottle_receipt import BottleReceipt
from app.models.bottle_return import BottleReturn
from app.models.order import Order, OrderStatus
from app.services import bottle_service, customer_service, order_service, stats_service


class TestOrderServiceCreate:
    def test_create_order(self, session, customer):
        order = order_service.create_order(
            session, customer.id, 5, "123 Main St", "Leave at door"
        )
        session.commit()
        assert order.id is not None
        assert order.bottle_count == 5
        assert order.status == OrderStatus.PENDING.value
        assert order.delivery_address == "123 Main St"
        assert order.delivery_notes == "Leave at door"
        assert len(order.status_logs) == 1

    def test_create_order_strips_whitespace(self, session, customer):
        order = order_service.create_order(
            session, customer.id, 3, "  Addr  ", "  Notes  "
        )
        session.commit()
        assert order.delivery_address == "Addr"
        assert order.delivery_notes == "Notes"

    def test_duplicate_order_cooldown(self, session, customer):
        order_service.create_order(session, customer.id, 5, "Addr")
        session.commit()
        with pytest.raises(ValueError, match="similar order"):
            order_service.create_order(session, customer.id, 5, "Addr")

    def test_max_pending_orders(self, session, customer):
        for i in range(3):
            order_service.create_order(session, customer.id, i + 1, f"Addr {i}")
            session.commit()
        with pytest.raises(ValueError, match="active orders"):
            order_service.create_order(session, customer.id, 10, "Addr")


class TestOrderServiceClaim:
    def test_claim_order(self, session, pending_order, admin):
        result = order_service.claim_order(session, pending_order.id, admin.id, 1)
        session.commit()
        assert result is not None
        assert result.status == OrderStatus.IN_PROGRESS.value
        assert result.admin_id == admin.id
        assert result.version == 2

    def test_claim_already_claimed(self, session, pending_order, admin, admin2):
        order_service.claim_order(session, pending_order.id, admin.id, 1)
        session.commit()
        result = order_service.claim_order(session, pending_order.id, admin2.id, 1)
        assert result is None  # version mismatch

    def test_claim_non_pending(self, session, in_progress_order, admin2):
        result = order_service.claim_order(session, in_progress_order.id, admin2.id, 1)
        assert result is None


class TestOrderServiceDeliver:
    def test_deliver_order(self, session, in_progress_order, admin, receipt):
        result = order_service.mark_delivered(
            session, in_progress_order.id, admin.id, 1
        )
        session.commit()
        assert result is not None
        assert result.status == OrderStatus.DELIVERED.value

    def test_deliver_insufficient_stock(self, session, customer, admin):
        # Admin has no stock
        o = Order(
            customer_id=customer.id,
            admin_id=admin.id,
            bottle_count=5,
            delivery_address="test",
            status=OrderStatus.IN_PROGRESS.value,
        )
        session.add(o)
        session.commit()
        with pytest.raises(ValueError, match="Insufficient stock"):
            order_service.mark_delivered(session, o.id, admin.id, 1)

    def test_deliver_wrong_admin(self, session, in_progress_order, admin2, receipt):
        result = order_service.mark_delivered(
            session, in_progress_order.id, admin2.id, 1
        )
        assert result is None


class TestOrderServiceCancel:
    def test_cancel_pending_by_customer(self, session, pending_order, customer):
        result = order_service.cancel_order(
            session,
            pending_order.id,
            expected_version=1,
            canceled_by="customer",
            customer_id=customer.id,
        )
        session.commit()
        assert result is not None
        assert result.status == OrderStatus.CANCELED.value
        assert result.canceled_by == "customer"

    def test_cancel_pending_by_admin(self, session, pending_order, admin):
        result = order_service.cancel_order(
            session,
            pending_order.id,
            expected_version=1,
            canceled_by="admin",
            admin_id=admin.id,
            reason="Out of stock",
        )
        session.commit()
        assert result is not None
        assert result.canceled_by == "admin"
        assert result.notes == "Out of stock"

    def test_customer_cannot_cancel_in_progress(self, session, in_progress_order, customer):
        result = order_service.cancel_order(
            session,
            in_progress_order.id,
            expected_version=1,
            canceled_by="customer",
            customer_id=customer.id,
        )
        assert result is None

    def test_admin_can_cancel_in_progress(self, session, in_progress_order, admin):
        result = order_service.cancel_order(
            session,
            in_progress_order.id,
            expected_version=1,
            canceled_by="admin",
            admin_id=admin.id,
        )
        session.commit()
        assert result is not None
        assert result.status == OrderStatus.CANCELED.value

    def test_cannot_cancel_delivered(self, session, delivered_order):
        result = order_service.cancel_order(
            session, delivered_order.id, expected_version=1, canceled_by="admin"
        )
        assert result is None

    def test_cancel_version_mismatch(self, session, pending_order):
        result = order_service.cancel_order(
            session, pending_order.id, expected_version=999, canceled_by="admin"
        )
        assert result is None


class TestOrderServiceReassign:
    def test_reassign_order(self, session, in_progress_order):
        result = order_service.reassign_order(session, in_progress_order.id, 1)
        session.commit()
        assert result is not None
        assert result.status == OrderStatus.PENDING.value
        assert result.admin_id is None

    def test_reassign_non_in_progress(self, session, pending_order):
        result = order_service.reassign_order(session, pending_order.id, 1)
        assert result is None


class TestOrderServiceQueries:
    def test_get_pending_orders(self, session, pending_order):
        items, total = order_service.get_pending_orders(session)
        assert total == 1
        assert items[0].id == pending_order.id

    def test_get_admin_active_orders(self, session, in_progress_order, admin):
        orders = order_service.get_admin_active_orders(session, admin.id)
        assert len(orders) == 1

    def test_get_customer_orders(self, session, pending_order, customer):
        items, total = order_service.get_customer_orders(session, customer.id)
        assert total == 1

    def test_get_customer_pending_orders(self, session, pending_order, customer):
        orders = order_service.get_customer_pending_orders(session, customer.id)
        assert len(orders) == 1

    def test_get_customer_last_delivered(self, session, delivered_order, customer):
        result = order_service.get_customer_last_delivered(session, customer.id)
        assert result is not None
        assert result.id == delivered_order.id

    def test_list_orders_with_filters(self, session, pending_order, in_progress_order):
        items, total = order_service.list_orders(
            session, status=OrderStatus.PENDING.value
        )
        assert total == 1
        assert items[0].id == pending_order.id


class TestBottleService:
    def test_get_admin_stock(self, session, admin, receipt):
        stock = bottle_service.get_admin_stock(session, admin.id)
        assert stock == 50

    def test_admin_stock_after_delivery(self, session, admin, customer, receipt):
        o = Order(
            customer_id=customer.id,
            admin_id=admin.id,
            bottle_count=10,
            delivery_address="test",
            status=OrderStatus.DELIVERED.value,
        )
        session.add(o)
        session.commit()
        stock = bottle_service.get_admin_stock(session, admin.id)
        assert stock == 40

    def test_get_admin_inventory(self, session, admin, receipt):
        inv = bottle_service.get_admin_inventory(session, admin.id)
        assert inv["total_received"] == 50
        assert inv["total_delivered"] == 0
        assert inv["current_stock"] == 50

    def test_get_customer_bottles(self, session, customer):
        stats = bottle_service.get_customer_bottles(session, customer.id)
        assert stats["total_ordered"] == 0
        assert stats["total_delivered"] == 0
        assert stats["bottles_in_hand"] == 0

    def test_customer_bottles_after_delivery(self, session, customer, admin, receipt):
        o = Order(
            customer_id=customer.id,
            admin_id=admin.id,
            bottle_count=10,
            delivery_address="test",
            status=OrderStatus.DELIVERED.value,
        )
        session.add(o)
        session.commit()
        stats = bottle_service.get_customer_bottles(session, customer.id)
        assert stats["total_delivered"] == 10
        assert stats["bottles_in_hand"] == 10

    def test_record_receipt(self, session, admin):
        r = bottle_service.record_receipt(session, admin.id, 25, "Test receipt")
        session.commit()
        assert r.id is not None
        assert r.quantity == 25

    def test_record_receipt_invalid_quantity(self, session, admin):
        with pytest.raises(ValueError, match="positive"):
            bottle_service.record_receipt(session, admin.id, 0)

    def test_record_return(self, session, customer, admin, receipt):
        # First deliver some bottles
        o = Order(
            customer_id=customer.id,
            admin_id=admin.id,
            bottle_count=10,
            delivery_address="test",
            status=OrderStatus.DELIVERED.value,
        )
        session.add(o)
        session.commit()

        ret = bottle_service.record_return(session, customer.id, admin.id, 5)
        session.commit()
        assert ret.id is not None
        assert ret.quantity == 5

        stats = bottle_service.get_customer_bottles(session, customer.id)
        assert stats["bottles_in_hand"] == 5

    def test_return_exceeds_in_hand(self, session, customer, admin):
        with pytest.raises(ValueError, match="Cannot return"):
            bottle_service.record_return(session, customer.id, admin.id, 10)

    def test_returns_dont_increase_stock(self, session, customer, admin, receipt):
        o = Order(
            customer_id=customer.id,
            admin_id=admin.id,
            bottle_count=10,
            delivery_address="test",
            status=OrderStatus.DELIVERED.value,
        )
        session.add(o)
        session.commit()

        bottle_service.record_return(session, customer.id, admin.id, 5)
        session.commit()

        stock = bottle_service.get_admin_stock(session, admin.id)
        assert stock == 40  # 50 received - 10 delivered = 40, returns don't add back

    def test_global_bottle_stats(self, session, admin, customer, receipt):
        o = Order(
            customer_id=customer.id,
            admin_id=admin.id,
            bottle_count=10,
            delivery_address="test",
            status=OrderStatus.DELIVERED.value,
        )
        session.add(o)
        session.commit()

        stats = bottle_service.get_global_bottle_stats(session)
        assert stats["total_received"] == 50
        assert stats["total_delivered"] == 10
        assert stats["admin_stock"] == 40
        assert stats["customer_in_hand"] == 10


class TestCustomerService:
    def test_register_customer(self, session):
        c = customer_service.register_customer(
            session, 777, "New User", "New Addr", "+7777777777"
        )
        session.commit()
        assert c.id is not None
        assert c.full_name == "New User"

    def test_register_duplicate_phone(self, session, customer):
        with pytest.raises(ValueError, match="already registered"):
            customer_service.register_customer(
                session, 888, "Other", "Addr", customer.phone
            )

    def test_normalize_phone(self):
        assert customer_service.normalize_phone("(123) 456-7890") == "1234567890"
        assert customer_service.normalize_phone("+1 234-567-8900") == "+12345678900"

    def test_validate_phone(self):
        assert customer_service.validate_phone("+1234567890") is True
        assert customer_service.validate_phone("123") is False

    def test_get_by_telegram_id(self, session, customer):
        found = customer_service.get_by_telegram_id(session, customer.telegram_id)
        assert found is not None
        assert found.id == customer.id

    def test_get_by_phone(self, session, customer):
        found = customer_service.get_by_phone(session, customer.phone)
        assert found is not None

    def test_update_customer(self, session, customer):
        updated = customer_service.update_customer(
            session, customer.id, full_name="Updated Name"
        )
        assert updated.full_name == "Updated Name"

    def test_search_customers(self, session, customer):
        results = customer_service.search_customers(session, "John")
        assert len(results) == 1

    def test_list_customers_pagination(self, session, customer, customer2):
        items, total = customer_service.list_customers(session, page=1, per_page=1)
        assert total == 2
        assert len(items) == 1


class TestStatsService:
    def test_global_stats(self, session, pending_order, customer, admin):
        stats = stats_service.get_global_stats(session)
        assert stats["total_orders"] == 1
        assert stats["pending_orders"] == 1
        assert stats["total_customers"] == 1
        assert stats["active_admins"] == 1

    def test_orders_by_day(self, session, pending_order):
        result = stats_service.get_orders_by_day(session, days=30)
        assert len(result) >= 1
        assert result[0]["count"] >= 1

    def test_orders_by_status(self, session, pending_order, delivered_order):
        result = stats_service.get_orders_by_status(session)
        assert result.get(OrderStatus.PENDING.value, 0) == 1
        assert result.get(OrderStatus.DELIVERED.value, 0) == 1

    def test_stale_orders(self, session, in_progress_order):
        # Fresh order, shouldn't be stale
        result = stats_service.get_stale_orders(session, hours=24)
        assert len(result) == 0

    def test_recent_activity(self, session, pending_order):
        from app.models.order_status_log import OrderStatusLog

        log = OrderStatusLog(
            order_id=pending_order.id,
            old_status=None,
            new_status=OrderStatus.PENDING.value,
        )
        session.add(log)
        session.commit()
        result = stats_service.get_recent_activity(session, limit=10)
        assert len(result) == 1
