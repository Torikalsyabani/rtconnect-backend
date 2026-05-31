"""
RTConnect - Pengumuman Routes
GET    /api/pengumuman          - list (warga & admin)
GET    /api/pengumuman/:id      - detail
POST   /api/pengumuman          - buat (admin)
PUT    /api/pengumuman/:id      - edit (admin)
DELETE /api/pengumuman/:id      - hapus (admin)
"""
from flask import Blueprint, request, jsonify, g
from db_helper import get_db
from auth import admin_required, login_required

pengumuman_bp = Blueprint("pengumuman", __name__, url_prefix="/api/pengumuman")


@pengumuman_bp.route("", methods=["GET"])
@login_required
def list_pengumuman():
    kategori = request.args.get("kategori", "").strip()
    db       = get_db()

    query  = "SELECT p.*, u.nama AS pembuat FROM pengumuman p JOIN users u ON p.dibuat_oleh=u.id WHERE p.aktif=1"
    params = []
    if kategori:
        query += " AND p.kategori=?"
        params.append(kategori)
    query += " ORDER BY p.tanggal DESC"

    rows = db.execute(query, params).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@pengumuman_bp.route("/<int:pid>", methods=["GET"])
@login_required
def get_pengumuman(pid):
    db  = get_db()
    row = db.execute(
        "SELECT p.*, u.nama AS pembuat FROM pengumuman p JOIN users u ON p.dibuat_oleh=u.id WHERE p.id=?",
        (pid,)
    ).fetchone()
    db.close()
    if not row:
        return jsonify({"error": "Pengumuman tidak ditemukan"}), 404
    return jsonify(dict(row))


@pengumuman_bp.route("", methods=["POST"])
@admin_required
def buat_pengumuman():
    data     = request.get_json(force=True)
    judul    = (data.get("judul") or "").strip()
    konten   = (data.get("konten") or "").strip()
    kategori = (data.get("kategori") or "Umum").strip()
    tanggal  = (data.get("tanggal") or "").strip()
    lokasi   = data.get("lokasi")

    if not all([judul, konten, tanggal]):
        return jsonify({"error": "Judul, konten, dan tanggal wajib diisi"}), 400

    db = get_db()
    cur = db.execute(
        "INSERT INTO pengumuman (judul,konten,kategori,tanggal,lokasi,dibuat_oleh) VALUES (?,?,?,?,?,?)",
        (judul, konten, kategori, tanggal, lokasi, g.user_id)
    )
    pid = cur.lastrowid
    db.commit()

    db.execute(
        "INSERT INTO aktivitas (user_id,aksi,detail) VALUES (?,?,?)",
        (g.user_id, "buat_pengumuman", judul)
    )
    db.commit()
    db.close()
    return jsonify({"message": "Pengumuman dibuat", "id": pid}), 201


@pengumuman_bp.route("/<int:pid>", methods=["PUT"])
@admin_required
def edit_pengumuman(pid):
    data     = request.get_json(force=True)
    judul    = data.get("judul")
    konten   = data.get("konten")
    kategori = data.get("kategori")
    tanggal  = data.get("tanggal")
    lokasi   = data.get("lokasi")
    aktif    = data.get("aktif")

    db = get_db()
    db.execute(
        """UPDATE pengumuman SET
           judul    = COALESCE(?, judul),
           konten   = COALESCE(?, konten),
           kategori = COALESCE(?, kategori),
           tanggal  = COALESCE(?, tanggal),
           lokasi   = COALESCE(?, lokasi),
           aktif    = COALESCE(?, aktif)
           WHERE id=?""",
        (judul, konten, kategori, tanggal, lokasi, aktif, pid)
    )
    db.commit()
    db.close()
    return jsonify({"message": "Pengumuman diperbarui"})


@pengumuman_bp.route("/<int:pid>", methods=["DELETE"])
@admin_required
def hapus_pengumuman(pid):
    db = get_db()
    db.execute("UPDATE pengumuman SET aktif=0 WHERE id=?", (pid,))
    db.commit()
    db.close()
    return jsonify({"message": "Pengumuman dihapus"})
