import csv
import io
import math
from datetime import datetime, timezone

from flask import Blueprint, Response, jsonify, request
from flask_login import login_required

from app.database import db
from app.services import bottle_service, customer_service, order_service

customers_api = Blueprint("customers_api", __name__, url_prefix="/api/v1")


@customers_api.route("/customers")
@login_required
def list_customers():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    search = request.args.get("search")
    is_active = request.args.get("is_active")
    sort = request.args.get("sort", "created_at")
    order = request.args.get("order", "desc")

    active_filter = None
    if is_active is not None:
        active_filter = is_active.lower() in ("true", "1", "yes")

    items, total = customer_service.list_customers(
        db.session, page=page, per_page=per_page, search=search, is_active=active_filter
    )
    pages = max(1, math.ceil(total / per_page))

    result = []
    for c in items:
        stats = bottle_service.get_customer_bottles(db.session, c.id)
        result.append(
            {
                "id": c.id,
                "full_name": c.full_name,
                "phone": c.phone,
                "address": c.address,
                "is_active": c.is_active,
                "total_orders": stats["total_ordered"],
                "bottles_in_hand": stats["bottles_in_hand"],
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
        )

    return jsonify(
        {"items": result, "total": total, "page": page, "per_page": per_page, "pages": pages}
    )


@customers_api.route("/customers/export")
@login_required
def export_customers():
    search = request.args.get("search")
    is_active = request.args.get("is_active")

    active_filter = None
    if is_active is not None:
        active_filter = is_active.lower() in ("true", "1", "yes")

    items, _ = customer_service.list_customers(
        db.session, page=1, per_page=10000, search=search, is_active=active_filter
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Full Name", "Phone", "Address", "Active",
        "Total Orders", "Bottles In Hand", "Created At",
    ])
    for c in items:
        stats = bottle_service.get_customer_bottles(db.session, c.id)
        writer.writerow([
            c.id,
            c.full_name,
            c.phone,
            c.address,
            c.is_active,
            stats["total_ordered"],
            stats["bottles_in_hand"],
            c.created_at.isoformat() if c.created_at else "",
        ])

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="customers_{today}.csv"'},
    )


@customers_api.route("/customers/<int:customer_id>")
@login_required
def get_customer(customer_id):
    customer = customer_service.get_by_id(db.session, customer_id)
    if not customer:
        return jsonify({"error": "Customer not found", "code": "NOT_FOUND"}), 404

    stats = bottle_service.get_customer_bottles(db.session, customer_id)
    return jsonify(
        {
            "id": customer.id,
            "full_name": customer.full_name,
            "phone": customer.phone,
            "address": customer.address,
            "is_active": customer.is_active,
            "bottle_stats": stats,
            "created_at": customer.created_at.isoformat() if customer.created_at else None,
        }
    )


@customers_api.route("/customers/<int:customer_id>", methods=["PATCH"])
@login_required
def update_customer(customer_id):
    customer = customer_service.get_by_id(db.session, customer_id)
    if not customer:
        return jsonify({"error": "Customer not found", "code": "NOT_FOUND"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON", "code": "BAD_REQUEST"}), 400

    allowed_fields = {"full_name", "phone", "address", "is_active"}
    updates = {k: v for k, v in data.items() if k in allowed_fields}

    if not updates:
        return jsonify({"error": "No valid fields to update", "code": "BAD_REQUEST"}), 400

    try:
        customer = customer_service.update_customer(db.session, customer_id, **updates)
        db.session.commit()
    except ValueError as e:
        return jsonify({"error": str(e), "code": "UNPROCESSABLE"}), 422

    return jsonify(
        {
            "id": customer.id,
            "full_name": customer.full_name,
            "phone": customer.phone,
            "address": customer.address,
            "is_active": customer.is_active,
        }
    )


@customers_api.route("/customers/<int:customer_id>/bottles")
@login_required
def customer_bottles(customer_id):
    customer = customer_service.get_by_id(db.session, customer_id)
    if not customer:
        return jsonify({"error": "Customer not found", "code": "NOT_FOUND"}), 404

    stats = bottle_service.get_customer_bottles(db.session, customer_id)
    return jsonify({"customer_id": customer_id, **stats})


@customers_api.route("/customers/<int:customer_id>/orders")
@login_required
def customer_orders(customer_id):
    page = request.args.get("page", 1, type=int)
    per_page = 20
    items, total = order_service.get_customer_orders(
        db.session, customer_id, limit=per_page, offset=(page - 1) * per_page
    )
    return jsonify(
        {
            "items": [
                {
                    "id": o.id,
                    "bottle_count": o.bottle_count,
                    "status": o.status,
                    "created_at": o.created_at.isoformat() if o.created_at else None,
                }
                for o in items
            ],
            "total": total,
        }
    )
