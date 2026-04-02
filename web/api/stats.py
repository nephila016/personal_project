from flask import Blueprint, jsonify
from flask_login import login_required

from app.database import db
from app.services import stats_service

stats_api = Blueprint("stats_api", __name__, url_prefix="/api/v1")


@stats_api.route("/stats")
@login_required
def global_stats():
    stats = stats_service.get_global_stats(db.session)
    return jsonify(stats)
