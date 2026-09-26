import os

from dotenv import load_dotenv
from flask import Flask

from routes import register_routes

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")
    app.config["SUPABASE_URL"] = os.getenv("SUPABASE_URL", "")
    app.config["SUPABASE_KEY"] = os.getenv("SUPABASE_KEY", "")

    register_routes(app)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
