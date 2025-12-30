from flask import Blueprint, render_template, request, redirect, session, flash
from services.user_service import get_user_by_email, create_user, verify_password, public_user_session

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/login")
def login_page():
    return render_template("login.html")


@auth_bp.post("/login")
def login_submit():
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    if not email or not password:
        flash("Completa email y contraseña.", "error")
        return redirect("/login")

    try:
        user = get_user_by_email(email)
    except Exception as e:
        flash(f"Error consultando usuario: {str(e)}", "error")
        return redirect("/login")

    if not user:
        flash("Usuario no encontrado.", "error")
        return redirect("/login")

    if not verify_password(user, password):
        flash("Contraseña incorrecta.", "error")
        return redirect("/login")

    session["user"] = public_user_session(user)
    flash("Sesion iniciada.", "success")

    next_url = request.args.get("next") or "/catalogo"
    return redirect(next_url)


@auth_bp.get("/register")
def register_page():
    return render_template("register.html")


@auth_bp.post("/register")
def register_submit():
    full_name = (request.form.get("full_name") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    phone = (request.form.get("phone") or "").strip()
    city = (request.form.get("city") or "").strip()
    address = (request.form.get("address") or "").strip()

    password = request.form.get("password") or ""
    password2 = request.form.get("password2") or ""

    if not full_name or not email or not phone or not city or not address or not password:
        flash("Completa todos los campos.", "error")
        return redirect("/register")

    if password != password2:
        flash("Las contraseñas no coinciden.", "error")
        return redirect("/register")

    existing = get_user_by_email(email)
    if existing:
        flash("Este email ya esta registrado.", "error")
        return redirect("/register")

    try:
        user = create_user(
            full_name=full_name,
            email=email,
            password=password,
            role="buyer",
            phone=phone,
            city=city,
            address=address
        )
    except Exception as e:
        flash(f"No se pudo crear el usuario: {str(e)}", "error")
        return redirect("/register")

    session["user"] = public_user_session(user)
    flash("Cuenta creada y sesion iniciada.", "success")

    next_url = request.args.get("next") or "/catalogo"
    return redirect(next_url)


@auth_bp.get("/logout")
def logout():
    session.pop("user", None)
    flash("Sesion cerrada.", "success")
    return redirect("/")
