"""
RTConnect Backend - Main Server
Mendukung PostgreSQL (production) dan SQLite (lokal)

Jalankan lokal (SQLite):
  python server.py

Jalankan dengan PostgreSQL:
  DATABASE_URL=postgresql://user:pass@host/db python server.py

Deploy ke Render:
  gunicorn -w 2 -b 0.0.0.0:$PORT server:app
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS

# ── Inisialisasi DB jika SQLite dan belum ada ───────────────
DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    DB_PATH = os.environ.get("DB_PATH", "rtconnect.db")
    if not os.path.exists(DB_PATH):
        from db_init import init_db
        init_db()

# ── Flask App ────────────────────────────────────────────────
app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # max 5 MB

# ── Daftarkan Blueprints ─────────────────────────────────────
from routes.auth_routes              import auth_bp
from routes.warga_routes             import warga_bp
from routes.pengumuman_routes        import pengumuman_bp
from routes.iuran_routes             import iuran_bp
from routes.surat_routes             import surat_bp
from routes.laporan_routes           import laporan_bp
from routes.keuangan_keamanan_routes import keuangan_bp, keamanan_bp
from routes.dashboard_routes         import dashboard_bp

app.register_blueprint(auth_bp)
app.register_blueprint(warga_bp)
app.register_blueprint(pengumuman_bp)
app.register_blueprint(iuran_bp)
app.register_blueprint(surat_bp)
app.register_blueprint(laporan_bp)
app.register_blueprint(keuangan_bp)
app.register_blueprint(keamanan_bp)
app.register_blueprint(dashboard_bp)


@app.route("/")
def index():
    db_mode = "PostgreSQL" if DATABASE_URL else "SQLite"
    return jsonify({
        "app"    : "RTConnect API",
        "rt"     : "RT 01 / RW 12 Kp. Maleber",
        "version": "2.0.0",
        "db"     : db_mode,
        "status" : "running",
    })


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint tidak ditemukan"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method tidak diizinkan"}), 405

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File terlalu besar (maksimal 5 MB)"}), 413

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Terjadi kesalahan server", "detail": str(e)}), 500


if __name__ == "__main__":
    PORT  = int(os.environ.get("PORT", 5000))
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    db_info = f"PostgreSQL ({DATABASE_URL[:30]}...)" if DATABASE_URL else f"SQLite ({os.environ.get('DB_PATH','rtconnect.db')})"
    print(f"🗄️  Database : {db_info}")
    print(f"🚀 Server   : http://0.0.0.0:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
