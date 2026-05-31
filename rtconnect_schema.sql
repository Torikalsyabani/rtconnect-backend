-- ============================================================
-- RTConnect - Schema PostgreSQL
-- Jalankan file ini di pgAdmin: klik kanan database → Query Tool
-- lalu paste semua isi file ini → klik tombol Run (F5)
-- ============================================================

-- ─────────────────────────────────────────────
-- USERS (warga + admin)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    nik         VARCHAR(16) UNIQUE NOT NULL,
    nama        TEXT        NOT NULL,
    no_hp       TEXT,
    alamat      TEXT,
    blok        TEXT,
    role        TEXT        NOT NULL DEFAULT 'warga',
    password    TEXT        NOT NULL,
    foto        TEXT,
    aktif       INTEGER     NOT NULL DEFAULT 1,
    created_at  TIMESTAMP   NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- PENGUMUMAN
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pengumuman (
    id          SERIAL PRIMARY KEY,
    judul       TEXT        NOT NULL,
    konten      TEXT        NOT NULL,
    kategori    TEXT        NOT NULL DEFAULT 'Umum',
    tanggal     TEXT        NOT NULL,
    lokasi      TEXT,
    dibuat_oleh INTEGER     NOT NULL REFERENCES users(id),
    aktif       INTEGER     NOT NULL DEFAULT 1,
    created_at  TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- IURAN
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS iuran (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER     NOT NULL REFERENCES users(id),
    periode     TEXT        NOT NULL,
    jenis       TEXT        NOT NULL DEFAULT 'Keamanan & Kebersihan',
    jumlah      INTEGER     NOT NULL DEFAULT 150000,
    status      TEXT        NOT NULL DEFAULT 'belum_bayar',
    tgl_bayar   TEXT,
    bukti_bayar TEXT,
    metode      TEXT,
    jatuh_tempo TEXT        NOT NULL,
    catatan     TEXT,
    catatan_admin TEXT,
    created_at  TIMESTAMP   NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- PENGAJUAN SURAT
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pengajuan_surat (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER     NOT NULL REFERENCES users(id),
    jenis_surat TEXT        NOT NULL,
    keperluan   TEXT        NOT NULL,
    status      TEXT        NOT NULL DEFAULT 'diajukan',
    catatan_rt  TEXT,
    dibuat_oleh INTEGER     REFERENCES users(id),
    created_at  TIMESTAMP   NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- LAPORAN WARGA
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS laporan (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER     NOT NULL REFERENCES users(id),
    judul       TEXT        NOT NULL,
    deskripsi   TEXT        NOT NULL,
    kategori    TEXT        NOT NULL DEFAULT 'Umum',
    foto        TEXT,
    status      TEXT        NOT NULL DEFAULT 'baru',
    catatan_rt  TEXT,
    created_at  TIMESTAMP   NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- KEUANGAN RT
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS keuangan (
    id          SERIAL PRIMARY KEY,
    jenis       TEXT        NOT NULL,
    kategori    TEXT        NOT NULL,
    deskripsi   TEXT        NOT NULL,
    jumlah      INTEGER     NOT NULL,
    tanggal     TEXT        NOT NULL,
    dibuat_oleh INTEGER     REFERENCES users(id),
    created_at  TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- JADWAL KEAMANAN
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS jadwal_keamanan (
    id          SERIAL PRIMARY KEY,
    tanggal     TEXT        NOT NULL,
    shift       TEXT        NOT NULL,
    petugas     TEXT        NOT NULL,
    status      TEXT        NOT NULL DEFAULT 'terjadwal',
    catatan     TEXT,
    created_at  TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- AKTIVITAS / AUDIT LOG
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS aktivitas (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER     REFERENCES users(id),
    aksi        TEXT        NOT NULL,
    detail      TEXT,
    created_at  TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- ============================================================
-- SEED DATA (data awal / demo)
-- Password admin123 dan warga123 sudah di-hash SHA-256
-- ============================================================

INSERT INTO users (nik, nama, no_hp, alamat, blok, role, password) VALUES
('3201010101010001', 'Admin RT 01',   '081234567890', 'Pos RT 01, Kp. Maleber', 'RT',   'admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9'),
('3201010101010002', 'Budi Santoso',  '081234567891', 'Blok A No. 01',          'A-01', 'warga', '6b21de8534cbd0297f5217e53625b14f2ff44f317b262d6ea001da397b7552ea'),
('3201010101010003', 'Siti Aminah',   '081234567892', 'Blok C No. 04',          'C-04', 'warga', '6b21de8534cbd0297f5217e53625b14f2ff44f317b262d6ea001da397b7552ea'),
('3201010101010004', 'Rudi Hermawan', '081234567893', 'Blok B No. 07',          'B-07', 'warga', '6b21de8534cbd0297f5217e53625b14f2ff44f317b262d6ea001da397b7552ea'),
('3201010101010005', 'Dewi Rahayu',   '081234567894', 'Blok D No. 12',          'D-12', 'warga', '6b21de8534cbd0297f5217e53625b14f2ff44f317b262d6ea001da397b7552ea'),
('3201010101010006', 'Ahmad Fauzi',   '081234567895', 'Blok A No. 15',          'A-15', 'warga', '6b21de8534cbd0297f5217e53625b14f2ff44f317b262d6ea001da397b7552ea')
ON CONFLICT (nik) DO NOTHING;

INSERT INTO pengumuman (judul, konten, kategori, tanggal, lokasi, dibuat_oleh) VALUES
('Kerja Bakti & Pemilihan Ketua RT', 'Seluruh warga diharapkan hadir pada acara kerja bakti dan pemilihan ketua RT. Acara di balai RT.', 'Rapat Warga', '2024-11-12', 'Balai RT 01', 1),
('Perbaikan Saluran Air Blok C & D', 'Perbaikan saluran air sedang berlangsung di Blok C dan D. Mohon maaf atas ketidaknyamanan.', 'Infrastruktur', '2024-11-01', NULL, 1),
('Program Penghijauan RT 01', 'Kami mengundang seluruh warga untuk berpartisipasi dalam program penghijauan. Bibit gratis di pos RT.', 'Lingkungan', '2024-11-20', 'Pos RT 01', 1);

INSERT INTO iuran (user_id, periode, jumlah, status, jatuh_tempo) VALUES
(2, '2024-11', 150000, 'belum_bayar', '2024-11-10'),
(3, '2024-11', 150000, 'belum_bayar', '2024-11-10'),
(4, '2024-11', 150000, 'belum_bayar', '2024-11-10'),
(5, '2024-11', 150000, 'lunas',       '2024-11-10'),
(6, '2024-11', 150000, 'lunas',       '2024-11-10'),
(2, '2024-10', 150000, 'lunas',       '2024-10-10'),
(3, '2024-10', 150000, 'lunas',       '2024-10-10'),
(4, '2024-10', 150000, 'lunas',       '2024-10-10'),
(5, '2024-10', 150000, 'lunas',       '2024-10-10'),
(6, '2024-10', 150000, 'lunas',       '2024-10-10');

INSERT INTO pengajuan_surat (user_id, jenis_surat, keperluan, status) VALUES
(2, 'Surat Pengantar KTP',          'Perpanjangan KTP',  'diproses'),
(3, 'Surat Keterangan Domisili',    'Melamar pekerjaan', 'selesai'),
(4, 'Surat Keterangan Usaha',       'Izin usaha warung', 'diajukan'),
(5, 'Surat Keterangan Tidak Mampu', 'Beasiswa anak',     'diajukan');

INSERT INTO laporan (user_id, judul, deskripsi, kategori, status) VALUES
(2, 'Lampu Jalan Mati',    'Lampu jalan depan blok A mati sejak 3 hari yang lalu', 'Infrastruktur', 'diproses'),
(3, 'Sampah Menumpuk',     'Tumpukan sampah di sudut blok C belum diangkut',        'Kebersihan',    'baru'),
(4, 'Orang Tidak Dikenal', 'Ada orang asing mondar-mandir malam hari di blok B',    'Keamanan',      'selesai');

INSERT INTO keuangan (jenis, kategori, deskripsi, jumlah, tanggal, dibuat_oleh) VALUES
('pemasukan',   'Iuran Keamanan',         'Iuran Keamanan Oktober 2024',        750000, '2024-10-15', 1),
('pemasukan',   'Iuran Sampah',           'Iuran Kebersihan Oktober 2024',      250000, '2024-10-15', 1),
('pengeluaran', 'Pemeliharaan Fasilitas', 'Perbaikan paving block jalan utama', 200000, '2024-10-20', 1),
('pengeluaran', 'Dana Sosial',            'Santunan warga sakit Pak Karno',     300000, '2024-10-25', 1),
('pemasukan',   'Iuran Keamanan',         'Iuran Keamanan November 2024',       300000, '2024-11-05', 1);

INSERT INTO jadwal_keamanan (tanggal, shift, petugas, status) VALUES
('2024-11-12', 'Malam', 'Pak Ruslan & Pak Udin', 'terjadwal'),
('2024-11-12', 'Pagi',  'Pak Slamet',            'terjadwal'),
('2024-11-11', 'Malam', 'Pak Jono & Pak Wanto',  'selesai'),
('2024-11-11', 'Pagi',  'Pak Karno',             'selesai');
