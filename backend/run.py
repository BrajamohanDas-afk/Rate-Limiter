import os
from app import create_app, db
from app.models import Client, RateLimitConfig, RequestLog  # noqa: F401 - for shell context
from dotenv import load_dotenv

load_dotenv()

app = create_app(os.environ.get("FLASK_ENV", "development"))


@app.shell_context_processor
def make_shell_context():
    return {"db": db, "Client": Client, "RateLimitConfig": RateLimitConfig, "RequestLog": RequestLog}


if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Dev shortcut — use `flask db upgrade` in production.
    app.run(
        debug=os.environ.get("FLASK_ENV", "development") == "development",
        port=int(os.environ.get("FLASK_RUN_PORT", "5000")),
    )
