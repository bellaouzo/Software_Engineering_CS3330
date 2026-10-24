# Hooks every blueprint up to the app. New blueprints get added here.
# Imports are inside so the route files load after the app exists.
def register_routes(app):
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.tickets import tickets_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(tickets_bp)
