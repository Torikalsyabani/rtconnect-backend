"""
RTConnect - Keuangan & Keamanan Routes

Keuangan:
GET  /api/keuangan          - list transaksi (admin)
POST /api/keuangan          - tambah transaksi (admin)
GET  /api/keuangan/summary  - ringkasan saldo & statistik (admin)

Keamanan:
GET  /api/keamanan          - jadwal keamanan (semua)
POST /api/keamanan          - tambah jadwal (admin)
PUT  /api/keamanan/:id      - edit jadwal (admin)
"""
from flask import Blueprint, request, jsonify, g
from db_helper import get_db
from auth import admin_required, login_required

keuangan_bp = Blueprint("keuangan", __name__, url_prefix="/api/keuangan")
keamanan_bp = Blueprint("keamanan", __name__, url_prefix="/api/keamanan")


# ════════════════════════════════════════════
# KEUANGAN
# ════════════════════════════════════════════

@keuangan_bp.route("", methods=["GET"])
@admin_required
def list_keuangan():
    jenis    = request.args.get("jenis", "").strip()
    kategori = request.args.get("kategori", "").strip()
    dari     = request.args.get("dari", "").strip()
    sampai   = request.args.get("sampai", "").strip()

    db     = get_db()
    query  = """
        SELECT k.*, u.nama AS dicatat_oleh_nama
        FROM keuangan k
        LEFT JOIN users u ON k.dibuat_oleh = u.id
        WHERE 1=1
    """
    params = []

    if jenis:
        query += " AND k.jenis = ?"
        params.append(jenis)
    if kategori:
        query += " AND k.kategori = ?"
        params.append(kategori)
    if dari:
        query += " AND k.tanggal >= ?"
        params.append(dari)
    if sampai:
        query += " AND k.tanggal <= ?"
        params.append(sampai)

    query += " ORDER BY k.tanggal DESC, k.created_at DESC"
    rows   = db.execute(query, params).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@keuangan_bp.route("", methods=["POST"])
@admin_required
def tambah_keuangan():
    data      = request.get_json(force=True)
    jenis     = (data.get("jenis") or "").strip()
    kategori  = (data.get("kategori") or "").strip()
    deskripsi = (data.get("deskripsi") or "").strip()
    jumlah    = data.get("jumlah")
    tanggal   = (data.get("tanggal") or "").strip()

    if not all([jenis, kategori, deskripsi, jumlah, tanggal]):
        return jsonify({"error": "Semua field wajib diisi"}), 400
    if jenis not in ("pemasukan", "pengeluaran"):
        return jsonify({"error": "Jenis harus 'pemasukan' atau 'pengeluaran'"}), 400

    db  = get_db()
    cur = db.execute(
        "INSERT INTO keuangan (jenis,kategori,deskripsi,jumlah,tanggal,dibuat_oleh) VALUES (?,?,?,?,?,?)",
        (jenis, kategori, deskripsi, int(jumlah), tanggal, g.user_id)
    )
    kid = cur.lastrowid
    db.commit()

    db.execute(
        "INSERT INTO aktivitas (user_id,aksi,detail) VALUES (?,?,?)",
        (g.user_id, "tambah_transaksi", f"{jenis}: {deskripsi} Rp{jumlah}")
    )
    db.commit()
    db.close()
    return jsonify({"message": "Transaksi berhasil ditambahkan", "id": kid}), 201


@keuangan_bp.route("/summary", methods=["GET"])
@admin_required
def summary_keuangan():
    db = get_db()

    total = db.execute("""
        SELECT
            SUM(CASE WHEN jenis='pemasukan'   THEN jumlah ELSE 0 END) AS total_masuk,
            SUM(CASE WHEN jenis='pengeluaran' THEN jumlah ELSE 0 END) AS total_keluar
        FROM keuangan
    """).fetchone()

    per_bulan = db.execute("""
        SELECT
            TO_CHAR(tanggal, 'YYYY-MM') AS bulan,
            SUM(CASE WHEN jenis='pemasukan'   THEN jumlah ELSE 0 END) AS masuk,
            SUM(CASE WHEN jenis='pengeluaran' THEN jumlah ELSE 0 END) AS keluar
        FROM keuangan
        GROUP BY bulan
        ORDER BY bulan DESC
        LIMIT 12
    """).fetchall()

    per_kategori = db.execute("""
        SELECT kategori,
               SUM(jumlah) AS total,
               COUNT(*) AS jumlah_transaksi
        FROM keuangan
        GROUP BY kategori
        ORDER BY total DESC
    """).fetchall()

    db.close()
    saldo = (total["total_masuk"] or 0) - (total["total_keluar"] or 0)
    return jsonify({
        "saldo"       : saldo,
        "total_masuk" : total["total_masuk"] or 0,
        "total_keluar": total["total_keluar"] or 0,
        "per_bulan"   : [dict(r) for r in per_bulan],
        "per_kategori": [dict(r) for r in per_kategori],
    })


# ════════════════════════════════════════════
# KEAMANAN
# ════════════════════════════════════════════

@keamanan_bp.route("", methods=["GET"])
@login_required
def list_keamanan():
    tanggal = request.args.get("tanggal", "").strip()
    db      = get_db()

    query  = "SELECT * FROM jadwal_keamanan WHERE 1=1"
    params = []
    if tanggal:
        query += " AND tanggal = ?"
        params.append(tanggal)

    query += " ORDER BY tanggal DESC, shift ASC"
    rows   = db.execute(query, params).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


@keamanan_bp.route("", methods=["POST"])
@admin_required
def tambah_jadwal():
    data    = request.get_json(force=True)
    tanggal = (data.get("tanggal") or "").strip()
    shift   = (data.get("shift") or "").strip()
    petugas = (data.get("petugas") or "").strip()
    catatan = data.get("catatan")

    if not all([tanggal, shift, petugas]):
        return jsonify({"error": "Tanggal, shift, dan petugas wajib diisi"}), 400
    if shift not in ("Pagi", "Sore", "Malam"):
        return jsonify({"error": "Shift harus Pagi / Sore / Malam"}), 400

    db  = get_db()
    cur = db.execute(
        "INSERT INTO jadwal_keamanan (tanggal,shift,petugas,catatan) VALUES (?,?,?,?)",
        (tanggal, shift, petugas, catatan)
    )
    kid = cur.lastrowid
    db.commit()
    db.close()
    return jsonify({"message": "Jadwal ditambahkan", "id": kid}), 201


@keamanan_bp.route("/<int:kid>", methods=["PUT"])
@admin_required
def edit_jadwal(kid):
    data    = request.get_json(force=True)
    tanggal = data.get("tanggal")
    shift   = data.get("shift")
    petugas = data.get("petugas")
    status  = data.get("status")
    catatan = data.get("catatan")

    db = get_db()
    db.execute(
        """UPDATE jadwal_keamanan SET
           tanggal = COALESCE(?, tanggal),
           shift   = COALESCE(?, shift),
           petugas = COALESCE(?, petugas),
           status  = COALESCE(?, status),
           catatan = COALESCE(?, catatan)
           WHERE id=?""",
        (tanggal, shift, petugas, status, catatan, kid)
    )
    db.commit()
    db.close()
    return jsonify({"message": "Jadwal diperbarui"})
