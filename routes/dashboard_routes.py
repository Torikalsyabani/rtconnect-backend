"""
RTConnect - Dashboard Routes
GET /api/dashboard/admin  - statistik ringkas untuk admin
GET /api/dashboard/warga  - info ringkas untuk warga
GET /api/dashboard/aktivitas - log aktivitas terbaru (admin)
"""
from flask import Blueprint, jsonify, g
from db_helper import get_db
from auth import admin_required, login_required

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.route("/admin", methods=["GET"])
@admin_required
def admin_summary():
    db = get_db()

    # Warga
    total_warga  = db.execute("SELECT COUNT(*) AS n FROM users WHERE role='warga' AND aktif=1").fetchone()["n"]

    # Iuran bulan ini
    iuran_bulan  = db.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status='lunas' THEN 1 ELSE 0 END) AS lunas,
            SUM(CASE WHEN status='belum' THEN 1 ELSE 0 END) AS belum,
            SUM(CASE WHEN status='menunggu_verifikasi' THEN 1 ELSE 0 END) AS menunggu,
            SUM(CASE WHEN status='lunas' THEN jumlah ELSE 0 END) AS terkumpul
        FROM iuran
        WHERE periode = strftime('%Y-%m', 'now')
    """).fetchone()

    # Pengajuan surat pending
    surat_pending = db.execute(
        "SELECT COUNT(*) AS n FROM pengajuan_surat WHERE status IN ('diajukan','diproses')"
    ).fetchone()["n"]

    # Laporan belum selesai
    laporan_open  = db.execute(
        "SELECT COUNT(*) AS n FROM laporan WHERE status IN ('baru','diproses')"
    ).fetchone()["n"]

    # Pengumuman aktif
    pengumuman_aktif = db.execute(
        "SELECT COUNT(*) AS n FROM pengumuman WHERE aktif=1"
    ).fetchone()["n"]

    # Keuangan
    keuangan = db.execute("""
        SELECT
            SUM(CASE WHEN jenis='pemasukan'   THEN jumlah ELSE 0 END) AS total_masuk,
            SUM(CASE WHEN jenis='pengeluaran' THEN jumlah ELSE 0 END) AS total_keluar
        FROM keuangan
    """).fetchone()

    saldo = (keuangan["total_masuk"] or 0) - (keuangan["total_keluar"] or 0)

    db.close()
    return jsonify({
        "total_warga"      : total_warga,
        "iuran_bulan_ini"  : dict(iuran_bulan),
        "surat_pending"    : surat_pending,
        "laporan_open"     : laporan_open,
        "pengumuman_aktif" : pengumuman_aktif,
        "saldo_kas"        : saldo,
    })


@dashboard_bp.route("/warga", methods=["GET"])
@login_required
def warga_summary():
    db = get_db()

    # Tagihan aktif
    tagihan = db.execute(
        "SELECT COUNT(*) AS n, SUM(jumlah) AS total FROM iuran WHERE user_id=? AND status!='lunas'",
        (g.user_id,)
    ).fetchone()

    # Surat aktif
    surat = db.execute(
        "SELECT COUNT(*) AS n FROM pengajuan_surat WHERE user_id=? AND status IN ('diajukan','diproses')",
        (g.user_id,)
    ).fetchone()

    # Pengumuman terbaru
    pengumuman = db.execute(
        "SELECT id,judul,kategori,tanggal FROM pengumuman WHERE aktif=1 ORDER BY tanggal DESC LIMIT 3"
    ).fetchall()

    db.close()
    return jsonify({
        "tagihan_aktif"  : {"jumlah": tagihan["n"], "total_rp": tagihan["total"] or 0},
        "surat_berjalan" : surat["n"],
        "pengumuman_terbaru": [dict(r) for r in pengumuman],
    })


@dashboard_bp.route("/aktivitas", methods=["GET"])
@admin_required
def log_aktivitas():
    db   = get_db()
    rows = db.execute("""
        SELECT a.*, u.nama AS nama_user
        FROM aktivitas a
        LEFT JOIN users u ON a.user_id = u.id
        ORDER BY a.created_at DESC
        LIMIT 50
    """).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])
