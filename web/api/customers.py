import math

from flask import Blueprint, jsonify, request
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

    items, total = customer_service.list_customers(
        db.session, page=page, per_page=per_page, search=search
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
