# RTConnect — Panduan Deploy & PostgreSQL

---

## OPSI A: Lokal dengan pgAdmin (PostgreSQL di komputer sendiri)

### Langkah 1 — Install PostgreSQL + pgAdmin
Download dan install dari: https://www.postgresql.org/download/
(pgAdmin sudah termasuk di dalam installer)

### Langkah 2 — Buat Database Baru di pgAdmin

1. Buka **pgAdmin**
2. Di panel kiri, klik kanan **Databases** → **Create** → **Database...**
3. Isi nama: `rtconnect`
4. Klik **Save**

### Langkah 3 — Jalankan Schema SQL

1. Klik kanan database `rtconnect` → **Query Tool**
2. Klik ikon folder (Open File) atau tekan `Ctrl+O`
3. Pilih file **`rtconnect_schema.sql`** dari folder ini
4. Klik tombol **▶ Run** (atau tekan `F5`)
5. Harusnya muncul: `INSERT 0 6` dst di bagian bawah

### Langkah 4 — Konfigurasi .env

Salin `.env.example` menjadi `.env`, lalu edit:
```
DATABASE_URL=postgresql://postgres:PASSWORD_KAMU@localhost:5432/rtconnect
SECRET_KEY=buat_string_acak_panjang_disini
```
Ganti `PASSWORD_KAMU` dengan password PostgreSQL kamu (yang diset saat install).

### Langkah 5 — Jalankan Server
```bash
pip install -r requirements.txt
python server.py
```

---

## OPSI B: Deploy ke Render.com (Gratis, Online)

### Langkah 1 — Push ke GitHub
```bash
git init
git add .
git commit -m "RTConnect backend"
# Buat repo baru di github.com, lalu:
git remote add origin https://github.com/USERNAME/rtconnect-backend.git
git push -u origin main
```

### Langkah 2 — Buat Web Service di Render

1. Buka https://render.com → Login/Daftar
2. Klik **New +** → **Web Service**
3. Hubungkan repo GitHub kamu
4. Isi pengaturan:
   - **Name:** `rtconnect-api`
   - **Runtime:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn -w 2 -b 0.0.0.0:$PORT server:app`
5. Klik **Create Web Service**

### Langkah 3 — Tambah PostgreSQL di Render

1. Klik **New +** → **PostgreSQL**
2. **Name:** `rtconnect-db`
3. **Plan:** Free
4. Klik **Create Database**
5. Setelah dibuat, salin **Internal Database URL**

### Langkah 4 — Set Environment Variables

Di Web Service → **Environment** → tambah:
```
DATABASE_URL  = [paste Internal Database URL dari step 3]
SECRET_KEY    = [buat string acak, min 32 karakter]
```

### Langkah 5 — Inisialisasi Database di Render

1. Di Web Service → **Shell** (tab)
2. Ketik:
   ```bash
   python db_init_pg.py
   ```
   Atau copy-paste isi `rtconnect_schema.sql` ke psql:
   ```bash
   psql $DATABASE_URL < rtconnect_schema.sql
   ```

### Langkah 6 — Set URL di Frontend

Setelah deploy selesai, Render memberi URL seperti:
```
https://rtconnect-api.onrender.com
```
Isi URL ini di kolom **Konfigurasi Backend URL** di file HTML frontend.

---

## OPSI C: Deploy ke Railway.app (Alternatif Render)

1. Buka https://railway.app → Login dengan GitHub
2. **New Project** → **Deploy from GitHub repo**
3. Pilih repo → Railway auto-detect Python
4. Tambah **PostgreSQL plugin**: klik **+ New** → **Database** → **PostgreSQL**
5. Di **Variables**, tambah:
   ```
   DATABASE_URL = ${{Postgres.DATABASE_URL}}
   SECRET_KEY   = string_acak_kamu
   PORT         = 5000
   ```
6. Railway akan auto-deploy dan beri URL publik

---

## OPSI D: Supabase (PostgreSQL Managed)

1. Buka https://supabase.com → New Project
2. Setelah project siap, buka **SQL Editor**
3. Copy-paste isi `rtconnect_schema.sql` → klik **Run**
4. Ambil connection string dari **Settings** → **Database** → **Connection string** (URI)
5. Paste ke `DATABASE_URL` di `.env` atau Render/Railway

---

## Koneksi String Format

```
# Local pgAdmin
postgresql://postgres:PASSWORD@localhost:5432/rtconnect

# Render (dari dashboard)
postgresql://user:pass@host.render.com/rtconnect

# Railway
postgresql://postgres:pass@host.railway.app:PORT/railway

# Supabase
postgresql://postgres:pass@db.PROJECT.supabase.co:5432/postgres
```

---

## Troubleshooting

| Error | Solusi |
|-------|--------|
| `psycopg2.OperationalError: could not connect` | Cek DATABASE_URL, pastikan PostgreSQL berjalan |
| `relation "users" does not exist` | Belum run schema SQL, jalankan `rtconnect_schema.sql` di pgAdmin |
| `duplicate key value violates unique constraint` | Data sudah ada, normal jika run schema 2x |
| `CORS error` di browser | Pastikan URL frontend match dengan origin |
| Render error `No module named psycopg2` | Pastikan `requirements.txt` ada `psycopg2-binary` |
