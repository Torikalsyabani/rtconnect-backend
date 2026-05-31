"""
RTConnect - Pengajuan Surat Routes
GET  /api/surat              - list (admin: semua, warga: milik sendiri)
POST /api/surat              - ajukan surat (warga) / buat manual (admin)
GET  /api/surat/:id          - detail
PUT  /api/surat/:id/status   - update status (admin)
"""
from flask import Blueprint, request, jsonify, g
from db_helper import get_db
from auth import admin_required, login_required

surat_bp = Blueprint("surat", __name__, url_prefix="/api/surat")

JENIS_VALID = [
    "Surat Pengantar KTP",
    "Surat Keterangan Domisili",
    "Surat Keterangan Tidak Mampu",
    "Surat Keterangan Usaha",
    "Surat Keterangan Kelahiran",
    "Surat Pengantar Nikah",
]


@surat_bp.route("", methods=["GET"])
@login_required
def list_surat():
    status = request.args.get("status", "").strip()

    db     = get_db()
    query  = """
        SELECT s.*, u.nama AS nama_warga, u.blok
        FROM pengajuan_surat s
        JOIN users u ON s.user_id = u.id
        WHERE 1=1
    """
    params = []

    if g.role != "admin":
        query += " AND s.user_id = ?"
        params.append(g.user_id)

    if status:
        query += " AND s.status = ?"
        params.append(status)

    query += " ORDER BY s.created_at DESC"
    rows   = db.execute(query, params).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@surat_bp.route("", methods=["POST"])
@login_required
def ajukan_surat():
    data        = request.get_json(force=True)
    jenis_surat = (data.get("jenis_surat") or "").strip()
    keperluan   = (data.get("keperluan") or "").strip()
    # Admin bisa ajukan atas nama warga lain
    target_uid  = data.get("user_id", g.user_id)

    if not jenis_surat or not keperluan:
        return jsonify({"error": "Jenis surat dan keperluan wajib diisi"}), 400
    if jenis_surat not in JENIS_VALID:
        return jsonify({"error": "Jenis surat tidak valid", "valid": JENIS_VALID}), 400

    # Warga tidak bisa ajukan atas nama orang lain
    if g.role != "admin":
        target_uid = g.user_id

    db  = get_db()
    cur = db.execute(
        """INSERT INTO pengajuan_surat (user_id, jenis_surat, keperluan, dibuat_oleh)
           VALUES (?,?,?,?)""",
        (target_uid, jenis_surat, keperluan, g.user_id)
    )
    sid = cur.lastrowid
    db.commit()

    db.execute(
        "INSERT INTO aktivitas (user_id,aksi,detail) VALUES (?,?,?)",
        (g.user_id, "ajukan_surat", jenis_surat)
    )
    db.commit()
    db.close()
    return jsonify({"message": "Surat berhasil diajukan", "id": sid}), 201


@surat_bp.route("/<int:sid>", methods=["GET"])
@login_required
def get_surat(sid):
    db  = get_db()
    row = db.execute(
        """SELECT s.*, u.nama AS nama_warga, u.blok, u.no_hp
           FROM pengajuan_surat s JOIN users u ON s.user_id=u.id
           WHERE s.id=?""",
        (sid,)
    ).fetchone()
    db.close()

    if not row:
        return jsonify({"error": "Surat tidak ditemukan"}), 404
    if g.role != "admin" and row["user_id"] != g.user_id:
        return jsonify({"error": "Akses ditolak"}), 403

    return jsonify(dict(row))


@surat_bp.route("/<int:sid>/status", methods=["PUT"])
@admin_required
def update_status_surat(sid):
    data       = request.get_json(force=True)
    status     = data.get("status")
    catatan_rt = data.get("catatan_rt")

    STATUS_VALID = ["diajukan", "diproses", "selesai", "ditolak"]
    if status not in STATUS_VALID:
        return jsonify({"error": f"Status harus salah satu dari {STATUS_VALID}"}), 400

    db = get_db()
    db.execute(
        """UPDATE pengajuan_surat SET
           status=?, catatan_rt=COALESCE(?,catatan_rt),
           updated_at=datetime('now','localtime')
           WHERE id=?""",
        (status, catatan_rt, sid)
    )
    db.commit()

    db.execute(
        "INSERT INTO aktivitas (user_id,aksi,detail) VALUES (?,?,?)",
        (g.user_id, "update_status_surat", f"Surat ID:{sid} → {status}")
    )
    db.commit()
    db.close()
    return jsonify({"message": f"Status surat diperbarui menjadi '{status}'"})
