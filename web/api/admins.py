from flask import Blueprint, jsonify, request
from flask_login import login_required

from app.database import db
from app.models.admin import Admin
from app.models.order import Order, OrderStatus
from app.services import bottle_service

admins_api = Blueprint("admins_api", __name__, url_prefix="/api/v1")


@admins_api.route("/admins")
@login_required
def list_admins():
    admins = db.session.query(Admin).order_by(Admin.created_at.desc()).all()
    result = []
    for a in admins:
        inv = bottle_service.get_admin_inventory(db.session, a.id)
        result.append(
            {
                "id": a.id,
                "telegram_id": a.telegram_id,
                "full_name": a.full_name,
                "phone": a.phone,
                "is_active": a.is_active,
                "current_stock": inv["current_stock"],
                "total_delivered": inv["total_delivered"],
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
        )
    return jsonify({"items": result, "total": len(result)})


@admins_api.route("/admins", methods=["POST"])
@login_required
def create_admin():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON", "code": "BAD_REQUEST"}), 400

    telegram_id = data.get("telegram_id")
    full_name = data.get("full_name")

    if not telegram_id or not full_name:
        return (
            jsonify({"error": "telegram_id and full_name required", "code": "BAD_REQUEST"}),
            400,
        )

    existing = db.session.query(Admin).filter(Admin.telegram_id == telegram_id).first()
    if existing:
        return (
            jsonify({"error": "Admin with this Telegram ID exists", "code": "CONFLICT"}),
            409,
        )

    admin = Admin(
        telegram_id=telegram_id,
        full_name=full_name,
        phone=data.get("phone"),
        telegram_username=data.get("telegram_username"),
    )
    db.session.add(admin)
    db.session.commit()

    return (
        jsonify(
            {
                "id": admin.id,
                "telegram_id": admin.telegram_id,
                "full_name": admin.full_name,
                "is_active": admin.is_active,
                "created_at": admin.created_at.isoformat(),
            }
        ),
        201,
    )


@admins_api.route("/admins/<int:admin_id>")
@login_required
def get_admin(admin_id):
    admin = db.session.get(Admin, admin_id)
    if not admin:
        return jsonify({"error": "Admin not found", "code": "NOT_FOUND"}), 404

    inv = bottle_service.get_admin_inventory(db.session, admin_id)
    return jsonify(
        {
            "id": admin.id,
            "telegram_id": admin.telegram_id,
            "full_name": admin.full_name,
            "phone": admin.phone,
            "is_active": admin.is_active,
            "inventory": inv,
        }
    )


@admins_api.route("/admins/<int:admin_id>", methods=["PATCH"])
@login_required
def update_admin(admin_id):
    admin = db.session.get(Admin, admin_id)
    if not admin:
        return jsonify({"error": "Admin not found", "code": "NOT_FOUND"}), 404

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON", "code": "BAD_REQUEST"}), 400

    allowed_fields = {"full_name", "phone", "telegram_username", "is_active"}
    for key, value in data.items():
        if key in allowed_fields:
            setattr(admin, key, value.strip() if isinstance(value, str) else value)

    db.session.commit()
    return jsonify(
        {
            "id": admin.id,
            "telegram_id": admin.telegram_id,
            "full_name": admin.full_name,
            "phone": admin.phone,
            "is_active": admin.is_active,
        }
    )


@admins_api.route("/admins/<int:admin_id>/stock")
@login_required
def admin_stock(admin_id):
    admin = db.session.get(Admin, admin_id)
    if not admin:
        return jsonify({"error": "Admin not found", "code": "NOT_FOUND"}), 404

    inv = bottle_service.get_admin_inventory(db.session, admin_id)
    return jsonify({"admin_id": admin_id, **inv})


@admins_api.route("/admins/<int:admin_id>", methods=["DELETE"])
@login_required
def deactivate_admin(admin_id):
    admin = db.session.get(Admin, admin_id)
    if not admin:
        return jsonify({"error": "Admin not found", "code": "NOT_FOUND"}), 404

    active_orders = (
        db.session.query(Order)
        .filter(
            Order.admin_id == admin_id,
            Order.status == OrderStatus.IN_PROGRESS.value,
        )
        .first()
    )
    if active_orders:
        return (
            jsonify(
                {
                    "error": "Admin has active orders. Reassign or cancel them first.",
                    "code": "UNPROCESSABLE",
                }
            ),
            422,
        )

    admin.is_active = False
    db.session.commit()
    return jsonify({"id": admin.id, "is_active": False, "message": "Admin deactivated"})
