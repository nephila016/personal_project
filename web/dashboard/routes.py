import math

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.database import db
from app.models.admin import Admin
from app.models.bottle_receipt import BottleReceipt
from app.models.bottle_return import BottleReturn
from app.models.customer import Customer
from app.models.order import Order, OrderStatus
from app.services import bottle_service, customer_service, order_service, stats_service
from web.auth.forms import AdminForm

dashboard_bp = Blueprint(
    "dashboard", __name__, url_prefix="/dashboard"
)


@dashboard_bp.before_request
@login_required
def require_login():
    pass


@dashboard_bp.route("/")
def index():
    stats = stats_service.get_global_stats(db.session)
    orders_by_status = stats_service.get_orders_by_status(db.session)
    orders_by_day = stats_service.get_orders_by_day(db.session, days=30)
    recent_activity = stats_service.get_recent_activity(db.session, limit=10)

    return render_template(
        "dashboard.html",
        stats=stats,
        orders_by_status=orders_by_status,
        orders_by_day=orders_by_day,
        recent_activity=recent_activity,
    )


@dashboard_bp.route("/orders")
def orders():
    page = request.args.get("page", 1, type=int)
    per_page = 20
    status = request.args.get("status", "")
    search = request.args.get("search", "")

    items, total = order_service.list_orders(
        db.session,
        page=page,
        per_page=per_page,
        status=status or None,
        search=search or None,
    )
    pages = max(1, math.ceil(total / per_page))

    return render_template(
        "orders.html",
        orders=items,
        total=total,
        page=page,
        pages=pages,
        per_page=per_page,
        filters={
            "status": status,
            "search": search,
            "date_from": request.args.get("date_from", ""),
            "date_to": request.args.get("date_to", ""),
        },
    )


@dashboard_bp.route("/orders/<int:order_id>")
def order_detail(order_id):
    order = order_service.get_order_with_logs(db.session, order_id)
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for("dashboard.orders"))

    return render_template("order_detail.html", order=order)


@dashboard_bp.route("/orders/<int:order_id>/update-status", methods=["POST"])
def update_order_status(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for("dashboard.orders"))

    new_status = request.form.get("status")
    note = request.form.get("note", "").strip()

    if new_status == OrderStatus.CANCELED.value:
        result = order_service.cancel_order(
            db.session,
            order_id,
            order.version,
            canceled_by="admin",
            reason=note or "Canceled by global admin",
        )
    elif new_status == OrderStatus.PENDING.value and order.status == OrderStatus.IN_PROGRESS.value:
        result = order_service.reassign_order(db.session, order_id, order.version)
    else:
        flash("Invalid status transition.", "warning")
        return redirect(url_for("dashboard.order_detail", order_id=order_id))

    if result:
        db.session.commit()
        flash(f"Order #{order_id} status updated.", "success")
    else:
        flash("Could not update order. It may have been modified.", "warning")

    return redirect(url_for("dashboard.order_detail", order_id=order_id))


@dashboard_bp.route("/customers")
def customers():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "")
    per_page = 20

    items, total = customer_service.list_customers(
        db.session, page=page, per_page=per_page, search=search or None
    )
    pages = max(1, math.ceil(total / per_page))

    customer_list = []
    for c in items:
        stats = bottle_service.get_customer_bottles(db.session, c.id)
        c.total_orders = stats["total_ordered"]
        c.bottles_in_hand = stats["bottles_in_hand"]
        customer_list.append(c)

    return render_template(
        "customers.html",
        customers=customer_list,
        total=total,
        page=page,
        pages=pages,
        filters={"search": search},
    )


@dashboard_bp.route("/customers/<int:customer_id>")
def customer_detail(customer_id):
    customer = customer_service.get_by_id(db.session, customer_id)
    if not customer:
        flash("Customer not found.", "danger")
        return redirect(url_for("dashboard.customers"))

    bottle_stats = bottle_service.get_customer_bottles(db.session, customer_id)
    orders, _ = order_service.get_customer_orders(db.session, customer_id, limit=10)

    return render_template(
        "customer_detail.html",
        customer=customer,
        bottle_stats=bottle_stats,
        orders=orders,
    )


@dashboard_bp.route("/customers/<int:customer_id>/toggle", methods=["POST"])
def toggle_customer(customer_id):
    customer = db.session.get(Customer, customer_id)
    if customer:
        customer.is_active = not customer.is_active
        db.session.commit()
        status = "activated" if customer.is_active else "deactivated"
        flash(f"Customer {customer.full_name} {status}.", "success")
    return redirect(url_for("dashboard.customer_detail", customer_id=customer_id))


@dashboard_bp.route("/admins")
def admins():
    admin_list = db.session.query(Admin).order_by(Admin.created_at.desc()).all()
    for a in admin_list:
        inv = bottle_service.get_admin_inventory(db.session, a.id)
        a.stock = inv["current_stock"]
        a.total_delivered = inv["total_delivered"]

    return render_template("admins.html", admins=admin_list)


@dashboard_bp.route("/admins/new", methods=["GET", "POST"])
def admin_new():
    form = AdminForm()
    if form.validate_on_submit():
        telegram_id = form.telegram_id.data.strip()
        full_name = form.full_name.data.strip()
        phone = (form.phone.data or "").strip()

        if not telegram_id or not full_name:
            flash("Telegram ID and Full Name are required.", "danger")
            return render_template("admin_form.html", form=form)

        try:
            tid = int(telegram_id)
        except ValueError:
            flash("Telegram ID must be a number.", "danger")
            return render_template("admin_form.html", form=form)

        existing = (
            db.session.query(Admin)
            .filter(Admin.telegram_id == tid)
            .first()
        )
        if existing:
            flash("Admin with this Telegram ID already exists.", "danger")
            return render_template("admin_form.html", form=form)

        admin = Admin(
            telegram_id=tid,
            full_name=full_name,
            phone=phone or None,
        )
        db.session.add(admin)
        db.session.commit()
        flash(f"Admin {full_name} added.", "success")
        return redirect(url_for("dashboard.admins"))

    return render_template("admin_form.html", form=form)


@dashboard_bp.route("/admins/<int:admin_id>")
def admin_detail(admin_id):
    admin = db.session.get(Admin, admin_id)
    if not admin:
        flash("Admin not found.", "danger")
        return redirect(url_for("dashboard.admins"))

    inventory = bottle_service.get_admin_inventory(db.session, admin_id)
    recent_orders = (
        db.session.query(Order)
        .filter(Order.admin_id == admin_id)
        .order_by(Order.created_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "admin_detail.html",
        admin=admin,
        inventory=inventory,
        recent_orders=recent_orders,
    )


@dashboard_bp.route("/admins/<int:admin_id>/toggle", methods=["POST"])
def toggle_admin(admin_id):
    admin = db.session.get(Admin, admin_id)
    if admin:
        if not admin.is_active or not (
            db.session.query(Order)
            .filter(
                Order.admin_id == admin_id,
                Order.status == OrderStatus.IN_PROGRESS.value,
            )
            .first()
        ):
            admin.is_active = not admin.is_active
            db.session.commit()
            status = "activated" if admin.is_active else "deactivated"
            flash(f"Admin {admin.full_name} {status}.", "success")
        else:
            flash(
                "Cannot deactivate admin with active orders. Reassign or cancel them first.",
                "danger",
            )
    return redirect(url_for("dashboard.admin_detail", admin_id=admin_id))


@dashboard_bp.route("/inventory")
def inventory():
    bottle_stats = bottle_service.get_global_bottle_stats(db.session)
    receipts = (
        db.session.query(BottleReceipt)
        .order_by(BottleReceipt.received_at.desc())
        .limit(20)
        .all()
    )
    returns = (
        db.session.query(BottleReturn)
        .order_by(BottleReturn.returned_at.desc())
        .limit(20)
        .all()
    )

    return render_template(
        "inventory.html",
        bottle_stats=bottle_stats,
        receipts=receipts,
        returns=returns,
    )
