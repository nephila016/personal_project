import pytest

from app.database import Base, db
from app.models.admin import Admin
from app.models.bottle_receipt import BottleReceipt
from app.models.bottle_return import BottleReturn
from app.models.customer import Customer
from app.models.global_admin import GlobalAdmin
from app.models.order import Order, OrderStatus
from app.models.order_status_log import OrderStatusLog
from web import create_app


@pytest.fixture()
def app():
    app = create_app("testing")
    with app.app_context():
        Base.metadata.create_all(db.engine)
        yield app
        db.session.remove()
        Base.metadata.drop_all(db.engine)


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def session(app):
    with app.app_context():
        yield db.session


@pytest.fixture()
def global_admin(session):
    admin = GlobalAdmin(
        username="testadmin",
        full_name="Test Global Admin",
        must_change_password=False,
    )
    admin.set_password("testpass123")
    session.add(admin)
    session.commit()
    return admin


@pytest.fixture()
def logged_in_client(client, global_admin):
    client.post("/login", data={
        "username": "testadmin",
        "password": "testpass123",
    })
    return client


@pytest.fixture()
def customer(session):
    c = Customer(
        telegram_id=100001,
        telegram_username="johndoe",
        full_name="John Doe",
        address="123 Main St",
        phone="+1234567890",
    )
    session.add(c)
    session.commit()
    return c


@pytest.fixture()
def customer2(session):
    c = Customer(
        telegram_id=100002,
        telegram_username="janedoe",
        full_name="Jane Doe",
        address="456 Oak Ave",
        phone="+9876543210",
    )
    session.add(c)
    session.commit()
    return c


@pytest.fixture()
def admin(session):
    a = Admin(
        telegram_id=200001,
        telegram_username="admin_bot",
        full_name="Bot Admin",
        phone="+1112223333",
    )
    session.add(a)
    session.commit()
    return a


@pytest.fixture()
def admin2(session):
    a = Admin(
        telegram_id=200002,
        telegram_username="admin_bot2",
        full_name="Bot Admin 2",
        phone="+4445556666",
    )
    session.add(a)
    session.commit()
    return a


@pytest.fixture()
def pending_order(session, customer, admin):
    o = Order(
        customer_id=customer.id,
        bottle_count=5,
        delivery_address="123 Main St",
        status=OrderStatus.PENDING.value,
    )
    session.add(o)
    session.commit()
    return o


@pytest.fixture()
def in_progress_order(session, customer, admin):
    o = Order(
        customer_id=customer.id,
        admin_id=admin.id,
        bottle_count=5,
        delivery_address="123 Main St",
        status=OrderStatus.IN_PROGRESS.value,
    )
    session.add(o)
    session.commit()
    return o


@pytest.fixture()
def delivered_order(session, customer, admin):
    o = Order(
        customer_id=customer.id,
        admin_id=admin.id,
        bottle_count=5,
        delivery_address="123 Main St",
        status=OrderStatus.DELIVERED.value,
    )
    session.add(o)
    session.commit()
    return o


@pytest.fixture()
def receipt(session, admin):
    r = BottleReceipt(admin_id=admin.id, quantity=50, notes="Initial stock")
    session.add(r)
    session.commit()
    return r
