"""
RTConnect - Data Warga Routes (Admin)
GET    /api/warga              - list semua warga
GET    /api/warga/:id          - detail warga
POST   /api/warga              - tambah warga
PUT    /api/warga/:id          - edit warga
DELETE /api/warga/:id          - nonaktifkan warga
GET    /api/warga/:id/iuran    - riwayat iuran warga
"""
from flask import Blueprint, request, jsonify, g
from db_helper import get_db
from auth import hash_password, admin_required, login_required

warga_bp = Blueprint("warga", __name__, url_prefix="/api/warga")


def row_to_dict(row):
    return dict(row) if row else None


@warga_bp.route("", methods=["GET"])
@admin_required
def list_warga():
    search = request.args.get("q", "").strip()
    blok   = request.args.get("blok", "").strip()

    db    = get_db()
    query = "SELECT id,nik,nama,no_hp,alamat,blok,role,aktif,created_at FROM users WHERE role='warga'"
    params = []

    if search:
        query += " AND (nama LIKE ? OR nik LIKE ? OR blok LIKE ?)"
        s = f"%{search}%"
        params += [s, s, s]
    if blok:
        query += " AND blok = ?"
        params.append(blok)

    query += " ORDER BY nama ASC"
    rows = db.execute(query, params).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@warga_bp.route("/<int:warga_id>", methods=["GET"])
@login_required
def get_warga(warga_id):
    # Warga hanya bisa lihat profil sendiri
    if g.role != "admin" and g.user_id != warga_id:
        return jsonify({"error": "Akses ditolak"}), 403

    db   = get_db()
    user = db.execute(
        "SELECT id,nik,nama,no_hp,alamat,blok,role,aktif,foto,created_at FROM users WHERE id=?",
        (warga_id,)
    ).fetchone()
    db.close()
    if not user:
        return jsonify({"error": "Warga tidak ditemukan"}), 404
    return jsonify(dict(user))


@warga_bp.route("", methods=["POST"])
@admin_required
def tambah_warga():
    data     = request.get_json(force=True)
    nik      = (data.get("nik") or "").strip()
    nama     = (data.get("nama") or "").strip()
    no_hp    = (data.get("no_hp") or "").strip()
    alamat   = (data.get("alamat") or "").strip()
    blok     = (data.get("blok") or "").strip()
    password = data.get("password", "warga123")
    role     = data.get("role", "warga")

    if not all([nik, nama]):
        return jsonify({"error": "NIK dan nama wajib diisi"}), 400

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE nik=?", (nik,)).fetchone()
    if existing:
        db.close()
        return jsonify({"error": "NIK sudah terdaftar"}), 409

    db.execute(
        "INSERT INTO users (nik,nama,no_hp,alamat,blok,role,password) VALUES (?,?,?,?,?,?,?)",
        (nik, nama, no_hp, alamat, blok, role, hash_password(password))
    )
    db.commit()

    # Log aktivitas
    db.execute(
        "INSERT INTO aktivitas (user_id,aksi,detail) VALUES (?,?,?)",
        (g.user_id, "tambah_warga", f"NIK: {nik}, Nama: {nama}")
    )
    db.commit()
    db.close()
    return jsonify({"message": "Warga berhasil ditambahkan"}), 201


@warga_bp.route("/<int:warga_id>", methods=["PUT"])
@admin_required
def edit_warga(warga_id):
    data   = request.get_json(force=True)
    nama   = data.get("nama")
    no_hp  = data.get("no_hp")
    alamat = data.get("alamat")
    blok   = data.get("blok")
    aktif  = data.get("aktif")

    db = get_db()
    db.execute(
        """UPDATE users SET
           nama   = COALESCE(?, nama),
           no_hp  = COALESCE(?, no_hp),
           alamat = COALESCE(?, alamat),
           blok   = COALESCE(?, blok),
           aktif  = COALESCE(?, aktif),
           updated_at = datetime('now','localtime')
           WHERE id = ?""",
        (nama, no_hp, alamat, blok, aktif, warga_id)
    )
    db.commit()
    db.close()
    return jsonify({"message": "Data warga diperbarui"})


@warga_bp.route("/<int:warga_id>", methods=["DELETE"])
@admin_required
def hapus_warga(warga_id):
    db = get_db()
    db.execute("UPDATE users SET aktif=0 WHERE id=?", (warga_id,))
    db.commit()
    db.close()
    return jsonify({"message": "Warga dinonaktifkan"})


@warga_bp.route("/<int:warga_id>/iuran", methods=["GET"])
@login_required
def riwayat_iuran_warga(warga_id):
    if g.role != "admin" and g.user_id != warga_id:
        return jsonify({"error": "Akses ditolak"}), 403

    db   = get_db()
    rows = db.execute(
        "SELECT * FROM iuran WHERE user_id=? ORDER BY periode DESC", (warga_id,)
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])
