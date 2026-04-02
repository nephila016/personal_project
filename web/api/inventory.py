from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.database import db
from app.models.bottle_receipt import BottleReceipt
from app.models.bottle_return import BottleReturn
from app.services import bottle_service

inventory_api = Blueprint("inventory_api", __name__, url_prefix="/api/v1")


@inventory_api.route("/inventory/overview")
@login_required
def overview():
    stats = bottle_service.get_global_bottle_stats(db.session)
    return jsonify(stats)


@inventory_api.route("/inventory/receipts")
@login_required
def receipts():
    page = request.args.get("page", 1, type=int)
    per_page = 20
    admin_id = request.args.get("admin_id", type=int)

    q = db.session.query(BottleReceipt)
    if admin_id:
        q = q.filter(BottleReceipt.admin_id == admin_id)

    total = q.count()
    items = (
        q.order_by(BottleReceipt.received_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return jsonify(
        {
            "items": [
                {
                    "id": r.id,
                    "admin": {"id": r.admin.id, "full_name": r.admin.full_name},
                    "quantity": r.quantity,
                    "notes": r.notes,
                    "received_at": r.received_at.isoformat() if r.received_at else None,
                }
                for r in items
            ],
            "total": total,
            "page": page,
            "per_page": per_page,
        }
    )


@inventory_api.route("/inventory/returns")
@login_required
def returns():
    page = request.args.get("page", 1, type=int)
    per_page = 20

    q = db.session.query(BottleReturn)
    total = q.count()
    items = (
        q.order_by(BottleReturn.returned_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return jsonify(
        {
            "items": [
                {
                    "id": r.id,
                    "customer": {"id": r.customer.id, "full_name": r.customer.full_name},
                    "admin": {"id": r.admin.id, "full_name": r.admin.full_name},
                    "quantity": r.quantity,
                    "notes": r.notes,
                    "returned_at": r.returned_at.isoformat() if r.returned_at else None,
                }
                for r in items
            ],
            "total": total,
            "page": page,
            "per_page": per_page,
        }
    )
