import math

from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.database import db
from app.services import order_service

orders_api = Blueprint("orders_api", __name__, url_prefix="/api/v1")


@orders_api.route("/orders")
@login_required
def list_orders():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)
    status = request.args.get("status")
    customer_id = request.args.get("customer_id", type=int)
    admin_id = request.args.get("admin_id", type=int)
    search = request.args.get("search")

    items, total = order_service.list_orders(
        db.session,
        page=page,
        per_page=per_page,
        status=status,
        customer_id=customer_id,
        admin_id=admin_id,
        search=search,
    )
    pages = max(1, math.ceil(total / per_page))

    return jsonify(
        {
            "items": [_order_to_dict(o) for o in items],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }
    )


@orders_api.route("/orders/<int:order_id>")
@login_required
def get_order(order_id):
    order = order_service.get_order_with_logs(db.session, order_id)
    if not order:
        return jsonify({"error": "Order not found", "code": "NOT_FOUND"}), 404
    return jsonify(_order_to_dict(order))


@orders_api.route("/orders/<int:order_id>/status", methods=["PATCH"])
@login_required
def update_order_status(order_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON", "code": "BAD_REQUEST"}), 400

    new_status = data.get("status")
    note = data.get("note", "")
    version = data.get("version")

    if not new_status or version is None:
        return (
            jsonify({"error": "status and version required", "code": "BAD_REQUEST"}),
            400,
        )

    try:
        if new_status == "canceled":
            result = order_service.cancel_order(
                db.session,
                order_id,
                version,
                canceled_by="admin",
                reason=note,
            )
        elif new_status == "pending":
            result = order_service.reassign_order(db.session, order_id, version)
        else:
            return (
                jsonify(
                    {
                        "error": f"Cannot set status to '{new_status}' from web",
                        "code": "UNPROCESSABLE",
                    }
                ),
                422,
            )
    except ValueError as e:
        return jsonify({"error": str(e), "code": "UNPROCESSABLE"}), 422

    if result is None:
        return (
            jsonify(
                {
                    "error": "Order was modified. Please refresh.",
                    "code": "CONFLICT",
                }
            ),
            409,
        )

    db.session.commit()
    return jsonify(_order_to_dict(result))


@orders_api.route("/orders/<int:order_id>/history")
@login_required
def order_history(order_id):
    order = order_service.get_order_with_logs(db.session, order_id)
    if not order:
        return jsonify({"error": "Order not found", "code": "NOT_FOUND"}), 404

    history = []
    for log in order.status_logs:
        history.append(
            {
                "old_status": log.old_status,
                "new_status": log.new_status,
                "changed_at": log.changed_at.isoformat() if log.changed_at else None,
                "note": log.note,
            }
        )
    return jsonify({"order_id": order_id, "history": history})


def _order_to_dict(order):
    d = {
        "id": order.id,
        "customer": {
            "id": order.customer.id,
            "full_name": order.customer.full_name,
            "phone": order.customer.phone,
        }
        if order.customer
        else None,
        "admin": {
            "id": order.admin.id,
            "full_name": order.admin.full_name,
        }
        if order.admin
        else None,
        "bottle_count": order.bottle_count,
        "delivery_address": order.delivery_address,
        "delivery_notes": order.delivery_notes,
        "status": order.status,
        "canceled_by": order.canceled_by,
        "notes": order.notes,
        "version": order.version,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
    }
    return d
