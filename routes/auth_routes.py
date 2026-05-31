"""
RTConnect - Auth Routes
POST /api/auth/login
POST /api/auth/register
GET  /api/auth/me
PUT  /api/auth/me
"""
from flask import Blueprint, request, jsonify, g
from db_helper import get_db
from auth import hash_password, create_token, login_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    nik      = (data.get("nik") or "").strip()
    password = (data.get("password") or "").strip()

    if not nik or not password:
        return jsonify({"error": "NIK dan password wajib diisi"}), 400

    db   = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE nik = ? AND aktif = 1", (nik,)
    ).fetchone()
    db.close()

    if not user or user["password"] != hash_password(password):
        return jsonify({"error": "NIK atau password salah"}), 401

    token = create_token(user["id"], user["role"])
    return jsonify({
        "token": token,
        "user": {
            "id":    user["id"],
            "nik":   user["nik"],
            "nama":  user["nama"],
            "no_hp": user["no_hp"],
            "alamat":user["alamat"],
            "blok":  user["blok"],
            "role":  user["role"],
            "foto":  user["foto"],
        }
    })


@auth_bp.route("/register", methods=["POST"])
def register():
    data   = request.get_json(force=True)
    nik    = (data.get("nik") or "").strip()
    nama   = (data.get("nama") or "").strip()
    no_hp  = (data.get("no_hp") or "").strip()
    alamat = (data.get("alamat") or "").strip()
    blok   = (data.get("blok") or "").strip()
    password = (data.get("password") or "").strip()

    if not all([nik, nama, password]):
        return jsonify({"error": "NIK, nama, dan password wajib diisi"}), 400
    if len(nik) != 16 or not nik.isdigit():
        return jsonify({"error": "NIK harus 16 digit angka"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password minimal 6 karakter"}), 400

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE nik = ?", (nik,)).fetchone()
    if existing:
        db.close()
        return jsonify({"error": "NIK sudah terdaftar"}), 409

    db.execute(
        "INSERT INTO users (nik, nama, no_hp, alamat, blok, role, password) VALUES (?,?,?,?,?,'warga',?)",
        (nik, nama, no_hp, alamat, blok, hash_password(password))
    )
    db.commit()
    user = db.execute("SELECT * FROM users WHERE nik = ?", (nik,)).fetchone()
    db.close()

    token = create_token(user["id"], "warga")
    return jsonify({
        "token": token,
        "user": {
            "id": user["id"], "nik": user["nik"], "nama": user["nama"],
            "role": user["role"]
        }
    }), 201


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    db   = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (g.user_id,)).fetchone()
    db.close()
    if not user:
        return jsonify({"error": "User tidak ditemukan"}), 404
    return jsonify({
        "id":    user["id"],
        "nik":   user["nik"],
        "nama":  user["nama"],
        "no_hp": user["no_hp"],
        "alamat":user["alamat"],
        "blok":  user["blok"],
        "role":  user["role"],
        "foto":  user["foto"],
        "created_at": user["created_at"],
    })


@auth_bp.route("/me", methods=["PUT"])
@login_required
def update_me():
    data   = request.get_json(force=True)
    nama   = data.get("nama")
    no_hp  = data.get("no_hp")
    alamat = data.get("alamat")

    db = get_db()
    db.execute(
        """UPDATE users SET nama=COALESCE(?,nama), no_hp=COALESCE(?,no_hp),
           alamat=COALESCE(?,alamat), updated_at=datetime('now','localtime')
           WHERE id=?""",
        (nama, no_hp, alamat, g.user_id)
    )
    db.commit()

    # Ganti password jika dikirim
    new_pw = data.get("password_baru")
    old_pw = data.get("password_lama")
    if new_pw and old_pw:
        user = db.execute("SELECT password FROM users WHERE id=?", (g.user_id,)).fetchone()
        if user["password"] != hash_password(old_pw):
            db.close()
            return jsonify({"error": "Password lama tidak sesuai"}), 400
        if len(new_pw) < 6:
            db.close()
            return jsonify({"error": "Password baru minimal 6 karakter"}), 400
        db.execute("UPDATE users SET password=? WHERE id=?", (hash_password(new_pw), g.user_id))
        db.commit()

    db.close()
    return jsonify({"message": "Profil berhasil diperbarui"})
