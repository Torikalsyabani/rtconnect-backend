"""
RTConnect - Iuran Routes
GET  /api/iuran                  - list iuran (admin: semua, warga: milik sendiri)
GET  /api/iuran/tagihan-saya     - tagihan aktif warga yg login
POST /api/iuran                  - generate tagihan (admin)
PUT  /api/iuran/:id/upload-bukti - upload bukti bayar (warga)
PUT  /api/iuran/:id/verifikasi   - verifikasi pembayaran (admin)
GET  /api/iuran/rekap            - rekap per periode (admin)
"""
import os
from flask import Blueprint, request, jsonify, g
from db_helper import get_db
from auth import admin_required, login_required
from cloudinary_helper import upload_file, allowed_file

iuran_bp = Blueprint("iuran", __name__, url_prefix="/api/iuran")


@iuran_bp.route("", methods=["GET"])
@login_required
def list_iuran():
    periode = request.args.get("periode", "").strip()
    status  = request.args.get("status", "").strip()
    user_id = request.args.get("user_id", "").strip()

    db     = get_db()
    query  = """
        SELECT i.*, u.nama, u.blok
        FROM iuran i
        JOIN users u ON i.user_id = u.id
        WHERE 1=1
    """
    params = []

    if g.role != "admin":
        query += " AND i.user_id = ?"
        params.append(g.user_id)
    elif user_id:
        query += " AND i.user_id = ?"
        params.append(user_id)

    if periode:
        query += " AND i.periode = ?"
        params.append(periode)
    if status:
        query += " AND i.status = ?"
        params.append(status)

    query += " ORDER BY i.created_at DESC"
    rows   = db.execute(query, params).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@iuran_bp.route("/tagihan-saya", methods=["GET"])
@login_required
def tagihan_saya():
    db   = get_db()
    rows = db.execute(
        "SELECT * FROM iuran WHERE user_id=? AND status IN ('belum_bayar','menunggu_verifikasi') ORDER BY jatuh_tempo",
        (g.user_id,)
    ).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@iuran_bp.route("", methods=["POST"])
@admin_required
def generate_tagihan():
    data        = request.get_json(force=True)
    periode     = (data.get("periode") or "").strip()
    jumlah      = data.get("jumlah")
    jenis       = (data.get("jenis") or "Iuran RT").strip()
    jatuh_tempo = (data.get("jatuh_tempo") or "").strip()
    user_ids    = data.get("user_ids")   # list atau None → semua warga aktif

    if not periode or not jumlah or not jatuh_tempo:
        return jsonify({"error": "periode, jumlah, dan jatuh_tempo wajib diisi"}), 400

    db = get_db()

    if not user_ids:
        rows     = db.execute("SELECT id FROM users WHERE role='warga' AND aktif=1").fetchall()
        user_ids = [r["id"] for r in rows]

    inserted = 0
    for uid in user_ids:
        existing = db.execute(
            "SELECT id FROM iuran WHERE user_id=? AND periode=? AND jenis=?",
            (uid, periode, jenis)
        ).fetchone()
        if not existing:
            db.execute(
                "INSERT INTO iuran (user_id,periode,jenis,jumlah,jatuh_tempo) VALUES (?,?,?,?,?)",
                (uid, periode, jenis, jumlah, jatuh_tempo)
            )
            inserted += 1

    db.commit()
    db.close()
    return jsonify({"message": f"{inserted} tagihan berhasil digenerate", "periode": periode}), 201


@iuran_bp.route("/<int:iid>/upload-bukti", methods=["PUT"])
@login_required
def upload_bukti(iid):
    db  = get_db()
    row = db.execute("SELECT * FROM iuran WHERE id=?", (iid,)).fetchone()

    if not row:
        db.close()
        return jsonify({"error": "Iuran tidak ditemukan"}), 404
    if g.role != "admin" and row["user_id"] != g.user_id:
        db.close()
        return jsonify({"error": "Akses ditolak"}), 403

    if "bukti" not in request.files:
        db.close()
        return jsonify({"error": "File bukti diperlukan"}), 400

    file = request.files["bukti"]
    if not allowed_file(file.filename):
        db.close()
        return jsonify({"error": "Format file tidak diizinkan (png/jpg/pdf)"}), 400

    try:
        url = upload_file(file, folder="bukti_bayar", public_id_prefix=f"iuran_{iid}")
    except Exception as e:
        db.close()
        return jsonify({"error": f"Gagal upload: {str(e)}"}), 500

    metode = request.form.get("metode", "transfer")
    db.execute(
        """UPDATE iuran SET status='menunggu_verifikasi', bukti_bayar=?,
           metode=?, tgl_bayar=date('now','localtime'), updated_at=datetime('now','localtime')
           WHERE id=?""",
        (url, metode, iid)
    )
    db.commit()
    db.close()
    return jsonify({"message": "Bukti bayar berhasil diupload", "bukti_url": url})


@iuran_bp.route("/<int:iid>/verifikasi", methods=["PUT"])
@admin_required
def verifikasi(iid):
    data   = request.get_json(force=True)
    status = data.get("status")
    catatan = data.get("catatan", "")

    if status not in ("lunas", "ditolak"):
        return jsonify({"error": "status harus 'lunas' atau 'ditolak'"}), 400

    db  = get_db()
    row = db.execute("SELECT * FROM iuran WHERE id=?", (iid,)).fetchone()
    if not row:
        db.close()
        return jsonify({"error": "Iuran tidak ditemukan"}), 404

    db.execute(
        """UPDATE iuran SET status=?, catatan_admin=?,
           updated_at=datetime('now','localtime') WHERE id=?""",
        (status, catatan, iid)
    )

    if status == "lunas":
        db.execute(
            "INSERT INTO keuangan (jenis,kategori,jumlah,keterangan,tanggal) VALUES (?,?,?,?,date('now','localtime'))",
            ("pemasukan", "Iuran", row["jumlah"], f"Iuran {row['periode']} - user #{row['user_id']}")
        )

    db.commit()
    db.close()
    return jsonify({"message": f"Iuran diverifikasi sebagai '{status}'"})


@iuran_bp.route("/rekap", methods=["GET"])
@admin_required
def rekap():
    periode = request.args.get("periode", "").strip()
    db      = get_db()

    query  = """
        SELECT i.periode, COUNT(*) total,
               SUM(CASE WHEN i.status='lunas' THEN 1 ELSE 0 END) lunas,
               SUM(CASE WHEN i.status='belum_bayar' THEN 1 ELSE 0 END) belum,
               SUM(CASE WHEN i.status='menunggu_verifikasi' THEN 1 ELSE 0 END) menunggu,
               SUM(CASE WHEN i.status='lunas' THEN i.jumlah ELSE 0 END) total_terkumpul
        FROM iuran i WHERE 1=1
    """
    params = []
    if periode:
        query += " AND i.periode = ?"
        params.append(periode)
    query += " GROUP BY i.periode ORDER BY i.periode DESC"

    rows = db.execute(query, params).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])
