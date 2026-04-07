"""Tests for database models: constraints, relationships, defaults."""
from datetime import datetime, timezone

import pytest

from app.database import db
from app.models.admin import Admin
from app.models.bottle_receipt import BottleReceipt
from app.models.bottle_return import BottleReturn
from app.models.customer import Customer
from app.models.global_admin import GlobalAdmin
from app.models.order import CanceledBy, Order, OrderStatus
from app.models.order_status_log import OrderStatusLog


class TestCustomerModel:
    def test_create_customer(self, session):
        c = Customer(
            telegram_id=999,
            full_name="Test User",
            address="Test Addr",
            phone="+1111111111",
        )
        session.add(c)
        session.commit()
        assert c.id is not None
        assert c.is_active is True
        assert c.notification_blocked is False
        assert c.created_at is not None
        assert c.updated_at is not None

    def test_customer_telegram_id_unique(self, session, customer):
        c2 = Customer(
            telegram_id=customer.telegram_id,
            full_name="Duplicate",
            address="Addr",
            phone="+2222222222",
        )
        session.add(c2)
        with pytest.raises(Exception):
            session.commit()
        session.rollback()

    def test_customer_phone_unique(self, session, customer):
        c2 = Customer(
            telegram_id=999999,
            full_name="Other",
            address="Addr",
            phone=customer.phone,
        )
        session.add(c2)
        with pytest.raises(Exception):
            session.commit()
        session.rollback()

    def test_customer_relationships(self, session, customer):
        o = Order(
            customer_id=customer.id,
            bottle_count=3,
            delivery_address="test",
            status=OrderStatus.PENDING.value,
        )
        session.add(o)
        session.commit()
        assert len(customer.orders) == 1
        assert customer.orders[0].bottle_count == 3


class TestAdminModel:
    def test_create_admin(self, session):
        a = Admin(
            telegram_id=888,
            full_name="Admin Test",
        )
        session.add(a)
        session.commit()
        assert a.id is not None
        assert a.is_active is True
        assert a.updated_at is not None

    def test_admin_telegram_id_unique(self, session, admin):
        a2 = Admin(telegram_id=admin.telegram_id, full_name="Dup")
        session.add(a2)
        with pytest.raises(Exception):
            session.commit()
        session.rollback()

    def test_admin_relationships(self, session, admin, customer, receipt):
        assert len(admin.bottle_receipts) == 1
        assert admin.bottle_receipts[0].quantity == 50


class TestGlobalAdminModel:
    def test_password_hashing(self, session):
        ga = GlobalAdmin(
            username="ga_test",
            full_name="GA Test",
        )
        ga.set_password("secret123")
        session.add(ga)
        session.commit()
        assert ga.check_password("secret123") is True
        assert ga.check_password("wrong") is False

    def test_account_lockout(self, session):
        ga = GlobalAdmin(
            username="locktest",
            full_name="Lock Test",
        )
        ga.set_password("pass")
        ga.locked_until = datetime(2099, 1, 1, tzinfo=timezone.utc)
        session.add(ga)
        session.commit()
        assert ga.is_locked() is True

    def test_not_locked_when_expired(self, session):
        ga = GlobalAdmin(
            username="notlocked",
            full_name="Not Locked",
        )
        ga.set_password("pass")
        ga.locked_until = datetime(2020, 1, 1, tzinfo=timezone.utc)
        session.add(ga)
        session.commit()
        assert ga.is_locked() is False

    def test_must_change_password_default(self, session):
        ga = GlobalAdmin(username="newga", full_name="New GA")
        ga.set_password("pass")
        session.add(ga)
        session.commit()
        assert ga.must_change_password is True


class TestOrderModel:
    def test_create_order_defaults(self, session, customer):
        o = Order(
            customer_id=customer.id,
            bottle_count=10,
            delivery_address="123 Test",
            status=OrderStatus.PENDING.value,
        )
        session.add(o)
        session.commit()
        assert o.version == 1
        assert o.canceled_by is None
        assert o.admin_id is None
        assert o.created_at is not None

    def test_order_status_enum(self, session, customer):
        o = Order(
            customer_id=customer.id,
            bottle_count=1,
            delivery_address="addr",
            status=OrderStatus.PENDING.value,
        )
        session.add(o)
        session.commit()
        assert o.status_enum == OrderStatus.PENDING

    def test_order_customer_relationship(self, session, pending_order, customer):
        assert pending_order.customer.id == customer.id
        assert pending_order in customer.orders

    def test_order_admin_relationship(self, session, in_progress_order, admin):
        assert in_progress_order.admin.id == admin.id

    def test_order_status_log_relationship(self, session, pending_order):
        log = OrderStatusLog(
            order_id=pending_order.id,
            old_status=None,
            new_status=OrderStatus.PENDING.value,
        )
        session.add(log)
        session.commit()
        assert len(pending_order.status_logs) == 1


class TestOrderStatusEnum:
    def test_all_statuses(self):
        assert OrderStatus.PENDING.value == "pending"
        assert OrderStatus.IN_PROGRESS.value == "in_progress"
        assert OrderStatus.DELIVERED.value == "delivered"
        assert OrderStatus.CANCELED.value == "canceled"

    def test_canceled_by_enum(self):
        assert CanceledBy.CUSTOMER.value == "customer"
        assert CanceledBy.ADMIN.value == "admin"
        assert CanceledBy.SYSTEM.value == "system"


class TestBottleReceipt:
    def test_create_receipt(self, session, admin):
        r = BottleReceipt(admin_id=admin.id, quantity=20, notes="test")
        session.add(r)
        session.commit()
        assert r.id is not None
        assert r.received_at is not None

    def test_receipt_admin_relationship(self, session, receipt, admin):
        assert receipt.admin.id == admin.id


class TestBottleReturn:
    def test_create_return(self, session, customer, admin):
        br = BottleReturn(
            customer_id=customer.id,
            admin_id=admin.id,
            quantity=5,
            notes="test return",
        )
        session.add(br)
        session.commit()
        assert br.id is not None
        assert br.returned_at is not None

    def test_return_relationships(self, session, customer, admin):
        br = BottleReturn(
            customer_id=customer.id,
            admin_id=admin.id,
            quantity=3,
        )
        session.add(br)
        session.commit()
        assert br.customer.id == customer.id
        assert br.admin.id == admin.id
        assert br in customer.bottle_returns
