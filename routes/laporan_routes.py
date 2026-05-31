"""
RTConnect - Laporan Warga Routes
GET  /api/laporan            - list
POST /api/laporan            - buat laporan (warga)
GET  /api/laporan/:id        - detail
PUT  /api/laporan/:id/status - update status (admin)
"""
from flask import Blueprint, request, jsonify, g
from db_helper import get_db
from auth import admin_required, login_required
from cloudinary_helper import upload_file, allowed_file

laporan_bp = Blueprint("laporan", __name__, url_prefix="/api/laporan")


@laporan_bp.route("", methods=["GET"])
@login_required
def list_laporan():
    status   = request.args.get("status", "").strip()
    kategori = request.args.get("kategori", "").strip()

    db     = get_db()
    query  = """
        SELECT l.*, u.nama AS nama_warga, u.blok
        FROM laporan l JOIN users u ON l.user_id=u.id
        WHERE 1=1
    """
    params = []

    if g.role != "admin":
        query += " AND l.user_id = ?"
        params.append(g.user_id)

    if status:
        query += " AND l.status = ?"
        params.append(status)
    if kategori:
        query += " AND l.kategori = ?"
        params.append(kategori)

    query += " ORDER BY l.created_at DESC"
    rows   = db.execute(query, params).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@laporan_bp.route("", methods=["POST"])
@login_required
def buat_laporan():
    foto_url = None

    if request.content_type and "multipart" in request.content_type:
        judul     = (request.form.get("judul") or "").strip()
        deskripsi = (request.form.get("deskripsi") or "").strip()
        kategori  = (request.form.get("kategori") or "Umum").strip()

        if "foto" in request.files:
            file = request.files["foto"]
            if file and allowed_file(file.filename):
                try:
                    foto_url = upload_file(
                        file, folder="laporan",
                        public_id_prefix=f"laporan_{g.user_id}"
                    )
                except Exception as e:
                    return jsonify({"error": f"Gagal upload foto: {str(e)}"}), 500
    else:
        data      = request.get_json(force=True)
        judul     = (data.get("judul") or "").strip()
        deskripsi = (data.get("deskripsi") or "").strip()
        kategori  = (data.get("kategori") or "Umum").strip()

    if not judul or not deskripsi:
        return jsonify({"error": "Judul dan deskripsi wajib diisi"}), 400

    db  = get_db()
    cur = db.execute(
        "INSERT INTO laporan (user_id,judul,deskripsi,kategori,foto) VALUES (?,?,?,?,?)",
        (g.user_id, judul, deskripsi, kategori, foto_url)
    )
    lid = cur.lastrowid
    db.execute(
        "INSERT INTO aktivitas (user_id,aksi,detail) VALUES (?,?,?)",
        (g.user_id, "buat_laporan", judul)
    )
    db.commit()
    db.close()
    return jsonify({"message": "Laporan berhasil dikirim", "id": lid}), 201


@laporan_bp.route("/<int:lid>", methods=["GET"])
@login_required
def get_laporan(lid):
    db  = get_db()
    row = db.execute(
        "SELECT l.*, u.nama AS nama_warga, u.blok FROM laporan l JOIN users u ON l.user_id=u.id WHERE l.id=?",
        (lid,)
    ).fetchone()
    db.close()

    if not row:
        return jsonify({"error": "Laporan tidak ditemukan"}), 404
    if g.role != "admin" and row["user_id"] != g.user_id:
        return jsonify({"error": "Akses ditolak"}), 403

    return jsonify(dict(row))


@laporan_bp.route("/<int:lid>/status", methods=["PUT"])
@admin_required
def update_status_laporan(lid):
    data       = request.get_json(force=True)
    status     = data.get("status")
    catatan_rt = data.get("catatan_rt")

    STATUS_VALID = ["baru", "diproses", "selesai"]
    if status not in STATUS_VALID:
        return jsonify({"error": f"Status harus salah satu dari {STATUS_VALID}"}), 400

    db = get_db()
    db.execute(
        """UPDATE laporan SET status=?, catatan_rt=COALESCE(?,catatan_rt),
           updated_at=datetime('now','localtime') WHERE id=?""",
        (status, catatan_rt, lid)
    )
    db.commit()
    db.close()
    return jsonify({"message": f"Status laporan diperbarui menjadi '{status}'"})
