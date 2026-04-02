from datetime import datetime, timedelta, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.database import db
from app.models.global_admin import GlobalAdmin
from config import Config
from web.auth.forms import ChangePasswordForm, LoginForm

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        admin = (
            db.session.query(GlobalAdmin)
            .filter(GlobalAdmin.username == form.username.data)
            .first()
        )

        if admin and admin.is_locked():
            flash("Account is locked. Try again later.", "danger")
            return render_template("login.html", form=form)

        if admin and admin.check_password(form.password.data):
            if not admin.is_active:
                flash("Account is deactivated.", "danger")
                return render_template("login.html", form=form)

            admin.failed_login_attempts = 0
            admin.last_login_at = datetime.now(timezone.utc)
            db.session.commit()

            login_user(admin)

            if admin.must_change_password:
                return redirect(url_for("auth.change_password"))

            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.index"))
        else:
            if admin:
                admin.failed_login_attempts += 1
                if admin.failed_login_attempts >= Config.LOGIN_MAX_ATTEMPTS:
                    admin.locked_until = datetime.now(timezone.utc) + timedelta(
                        minutes=Config.LOGIN_LOCKOUT_MINUTES
                    )
                    flash("Too many failed attempts. Account locked.", "danger")
                db.session.commit()
            flash("Invalid username or password.", "danger")

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        current_user.set_password(form.new_password.data)
        current_user.must_change_password = False
        db.session.commit()
        flash("Password changed successfully.", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("change_password.html", form=form)
