"""
RTConnect - Database Initialization
Warga Kp.Maleber RT 01/05
"""
import sqlite3
import hashlib
import os

DB_PATH = os.environ.get("DB_PATH", "rtconnect.db")

SCHEMA = """
PRAGMA foreign_keys = ON;

-- ─────────────────────────────────────────────
-- USERS (warga + admin)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nik         TEXT    UNIQUE NOT NULL,          -- 16-digit NIK
    nama        TEXT    NOT NULL,
    no_hp       TEXT,
    alamat      TEXT,
    blok        TEXT,                             -- contoh: A-12
    role        TEXT    NOT NULL DEFAULT 'warga', -- 'warga' | 'admin'
    password    TEXT    NOT NULL,
    foto        TEXT,                             -- path file foto
    aktif       INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ─────────────────────────────────────────────
-- PENGUMUMAN
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pengumuman (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    judul       TEXT    NOT NULL,
    konten      TEXT    NOT NULL,
    kategori    TEXT    NOT NULL DEFAULT 'Umum',  -- Rapat Warga | Infrastruktur | Lingkungan | Umum
    tanggal     TEXT    NOT NULL,
    lokasi      TEXT,
    dibuat_oleh INTEGER NOT NULL REFERENCES users(id),
    aktif       INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ─────────────────────────────────────────────
-- IURAN (tagihan per warga per periode)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS iuran (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    periode     TEXT    NOT NULL,                 -- 'YYYY-MM' contoh '2024-11'
    jenis       TEXT    NOT NULL DEFAULT 'Keamanan & Kebersihan',
    jumlah      INTEGER NOT NULL DEFAULT 150000,
    status      TEXT    NOT NULL DEFAULT 'belum', -- 'belum' | 'menunggu_verifikasi' | 'lunas'
    tgl_bayar   TEXT,
    bukti_bayar TEXT,                             -- path file bukti
    metode      TEXT,                             -- 'transfer' | 'qris' | 'tunai'
    jatuh_tempo TEXT    NOT NULL,
    catatan     TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ─────────────────────────────────────────────
-- PENGAJUAN SURAT
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pengajuan_surat (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    jenis_surat TEXT    NOT NULL,
    keperluan   TEXT    NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'diajukan', -- diajukan | diproses | selesai | ditolak
    catatan_rt  TEXT,
    dibuat_oleh INTEGER REFERENCES users(id),    -- untuk surat manual oleh admin
    created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ─────────────────────────────────────────────
-- LAPORAN WARGA
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS laporan (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    judul       TEXT    NOT NULL,
    deskripsi   TEXT    NOT NULL,
    kategori    TEXT    NOT NULL DEFAULT 'Umum',  -- Keamanan | Infrastruktur | Kebersihan | Umum
    foto        TEXT,
    status      TEXT    NOT NULL DEFAULT 'baru',  -- baru | diproses | selesai
    catatan_rt  TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ─────────────────────────────────────────────
-- KEUANGAN RT (kas masuk/keluar)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS keuangan (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    jenis       TEXT    NOT NULL,   -- 'pemasukan' | 'pengeluaran'
    kategori    TEXT    NOT NULL,   -- Iuran Keamanan | Iuran Sampah | Pemeliharaan Fasilitas | Dana Sosial
    deskripsi   TEXT    NOT NULL,
    jumlah      INTEGER NOT NULL,
    tanggal     TEXT    NOT NULL,
    dibuat_oleh INTEGER REFERENCES users(id),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ─────────────────────────────────────────────
-- JADWAL KEAMANAN (piket/ronda)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS jadwal_keamanan (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tanggal     TEXT    NOT NULL,
    shift       TEXT    NOT NULL,   -- 'Pagi' | 'Sore' | 'Malam'
    petugas     TEXT    NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'terjadwal', -- terjadwal | selesai
    catatan     TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- ─────────────────────────────────────────────
-- AKTIVITAS / AUDIT LOG
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS aktivitas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER REFERENCES users(id),
    aksi        TEXT    NOT NULL,
    detail      TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);
"""

SEED_SQL = """
-- Admin default
INSERT OR IGNORE INTO users (nik, nama, no_hp, alamat, blok, role, password)
VALUES (
    '3201010101010001',
    'Admin RT 01',
    '081234567890',
    'Pos RT 01, Kp. Maleber',
    'RT',
    'admin',
    '{admin_hash}'
);

-- Beberapa warga contoh
INSERT OR IGNORE INTO users (nik, nama, no_hp, alamat, blok, role, password)
VALUES
    ('3201010101010002', 'Budi Santoso',    '081234567891', 'Blok A No. 01', 'A-01', 'warga', '{warga_hash}'),
    ('3201010101010003', 'Siti Aminah',     '081234567892', 'Blok C No. 04', 'C-04', 'warga', '{warga_hash}'),
    ('3201010101010004', 'Rudi Hermawan',   '081234567893', 'Blok B No. 07', 'B-07', 'warga', '{warga_hash}'),
    ('3201010101010005', 'Dewi Rahayu',     '081234567894', 'Blok D No. 12', 'D-12', 'warga', '{warga_hash}'),
    ('3201010101010006', 'Ahmad Fauzi',     '081234567895', 'Blok A No. 15', 'A-15', 'warga', '{warga_hash}');

-- Pengumuman contoh
INSERT OR IGNORE INTO pengumuman (judul, konten, kategori, tanggal, lokasi, dibuat_oleh)
VALUES
    ('Kerja Bakti Rutin & Pemilihan Ketua RT Baru',
     'Seluruh warga diharapkan hadir pada acara kerja bakti dan pemilihan ketua RT yang baru. Acara akan dilaksanakan di balai RT.',
     'Rapat Warga', '2024-11-12 08:00', 'Balai RT 01', 1),
    ('Perbaikan Saluran Air di Blok C dan D',
     'Perbaikan saluran air sedang berlangsung di Blok C dan D. Mohon maaf atas ketidaknyamanan selama proses perbaikan.',
     'Infrastruktur', '2024-11-01', NULL, 1),
    ('Program Penghijauan RT 01',
     'Kami mengundang seluruh warga untuk berpartisipasi dalam program penghijauan. Bibit tanaman tersedia gratis di pos RT.',
     'Lingkungan', '2024-11-20', 'Pos RT 01', 1);

-- Iuran November 2024 untuk semua warga
INSERT OR IGNORE INTO iuran (user_id, periode, jumlah, status, jatuh_tempo)
VALUES
    (2, '2024-11', 150000, 'belum',  '2024-11-10'),
    (3, '2024-11', 150000, 'belum',  '2024-11-10'),
    (4, '2024-11', 150000, 'belum',  '2024-11-10'),
    (5, '2024-11', 150000, 'lunas',  '2024-11-10'),
    (6, '2024-11', 150000, 'lunas',  '2024-11-10');

-- Iuran Oktober 2024 (sudah lunas semua)
INSERT OR IGNORE INTO iuran (user_id, periode, jumlah, status, tgl_bayar, jatuh_tempo)
VALUES
    (2, '2024-10', 150000, 'lunas', '2024-10-05', '2024-10-10'),
    (3, '2024-10', 150000, 'lunas', '2024-10-03', '2024-10-10'),
    (4, '2024-10', 150000, 'lunas', '2024-10-07', '2024-10-10'),
    (5, '2024-10', 150000, 'lunas', '2024-10-04', '2024-10-10'),
    (6, '2024-10', 150000, 'lunas', '2024-10-08', '2024-10-10');

-- Pengajuan surat contoh
INSERT OR IGNORE INTO pengajuan_surat (user_id, jenis_surat, keperluan, status)
VALUES
    (2, 'Surat Pengantar KTP',          'Perpanjangan KTP',       'diproses'),
    (3, 'Surat Keterangan Domisili',    'Melamar pekerjaan',      'selesai'),
    (4, 'Surat Keterangan Usaha',       'Izin usaha warung',      'diajukan'),
    (5, 'Surat Keterangan Tidak Mampu', 'Beasiswa anak',          'diajukan');

-- Laporan warga contoh
INSERT OR IGNORE INTO laporan (user_id, judul, deskripsi, kategori, status)
VALUES
    (2, 'Lampu Jalan Mati',       'Lampu jalan depan blok A mati sejak 3 hari yang lalu', 'Infrastruktur', 'diproses'),
    (3, 'Sampah Menumpuk',        'Tumpukan sampah di sudut blok C belum diangkut',        'Kebersihan',    'baru'),
    (4, 'Orang Tidak Dikenal',    'Ada orang asing mondar-mandir malam hari di blok B',    'Keamanan',      'selesai');

-- Keuangan contoh
INSERT OR IGNORE INTO keuangan (jenis, kategori, deskripsi, jumlah, tanggal, dibuat_oleh)
VALUES
    ('pemasukan',   'Iuran Keamanan',         'Iuran Keamanan Oktober 2024',          750000, '2024-10-15', 1),
    ('pemasukan',   'Iuran Sampah',           'Iuran Kebersihan Oktober 2024',         250000, '2024-10-15', 1),
    ('pengeluaran', 'Pemeliharaan Fasilitas', 'Perbaikan paving block jalan utama',   200000, '2024-10-20', 1),
    ('pengeluaran', 'Dana Sosial',            'Santunan warga sakit Pak Karno',       300000, '2024-10-25', 1),
    ('pemasukan',   'Iuran Keamanan',         'Iuran Keamanan November 2024',          300000, '2024-11-05', 1);

-- Jadwal keamanan contoh
INSERT OR IGNORE INTO jadwal_keamanan (tanggal, shift, petugas, status)
VALUES
    ('2024-11-12', 'Malam', 'Pak Ruslan & Pak Udin',  'terjadwal'),
    ('2024-11-12', 'Pagi',  'Pak Slamet',             'terjadwal'),
    ('2024-11-11', 'Malam', 'Pak Jono & Pak Wanto',   'selesai'),
    ('2024-11-11', 'Pagi',  'Pak Karno',              'selesai');
"""


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    admin_hash = hash_password("admin123")
    warga_hash = hash_password("warga123")
    seed = SEED_SQL.replace("{admin_hash}", admin_hash).replace("{warga_hash}", warga_hash)

    conn.executescript(seed)
    conn.commit()
    conn.close()
    print(f"✅ Database '{DB_PATH}' berhasil diinisialisasi.")
    print("   Admin  : NIK 3201010101010001 | password: admin123")
    print("   Warga  : NIK 3201010101010002 | password: warga123")


if __name__ == "__main__":
    init_db()
