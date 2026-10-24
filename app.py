import os

from dotenv import load_dotenv
from flask import Flask

from routes import register_routes

# Pull FLASK_SECRET_KEY and the Supabase keys out of .env so we don't hardcode them
load_dotenv()


# Builds the Flask app, loads the config, and hooks up all the routes
def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")
    app.config["SUPABASE_URL"] = os.getenv("SUPABASE_URL", "")
    app.config["SUPABASE_KEY"] = os.getenv("SUPABASE_KEY", "")

    register_routes(app)

    # Quick check that the app is up (dev.py waits on this before opening the browser)
    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


# Top level so gunicorn can find it as app:app
app = create_app()


# Only runs when started directly, debug mode reloads on save
if __name__ == "__main__":
    app.run(debug=True)
