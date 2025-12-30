from functools import wraps
from flask import session, redirect, request, flash

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user"):
            flash("Debes iniciar sesion para continuar.", "warning")
            return redirect(f"/login?next={request.path}")
        return view(*args, **kwargs)
    return wrapped
