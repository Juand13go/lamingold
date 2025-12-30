import os
from flask import Flask
from dotenv import load_dotenv
from routes.checkout import checkout_bp
from routes.shop import shop_bp
from routes.cart import cart_bp
from routes.auth import auth_bp
from routes.admin import admin_bp
# from routes.pages import pages_bp

load_dotenv()  # carga .env

def create_app():
    app = Flask(__name__)

    # SECRET KEY para session (carrito)
    app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key_change_me")

    # Registrar blueprints
    app.register_blueprint(shop_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    # app.register_blueprint(pages_bp)

    # Debug: lista rutas registradas
    @app.get("/debug/routes")
    def debug_routes():
        return "\n".join(sorted([str(r) for r in app.url_map.iter_rules()])), 200, {
            "Content-Type": "text/plain; charset=utf-8"
        }

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
