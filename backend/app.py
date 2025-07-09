from flask import Flask, send_from_directory
from flask_cors import CORS
from routes.ask import ask_bp
from routes.upload import upload_bp
from routes.related import related_bp
import os

app = Flask(__name__, static_folder="../frontend/react-ui/build", static_url_path="/")
CORS(app)

app.register_blueprint(ask_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(related_bp)

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_react(path):
    static_dir = app.static_folder or os.path.join(os.getcwd(), "frontend", "react-ui", "build")
    
    full_path = os.path.join(static_dir, path)

    if path and os.path.exists(full_path):
        return send_from_directory(static_dir, path)
    else:
        return send_from_directory(static_dir, "index.html")

if __name__ == "__main__":
    app.run(port=5678, debug=True)