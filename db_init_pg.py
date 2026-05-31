"""
RTConnect - Inisialisasi database PostgreSQL
Jalankan sekali setelah deploy:
  python db_init_pg.py
"""
import os
import hashlib
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    print("❌ DATABASE_URL tidak diset di environment!")
    exit(1)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def run():
    # Baca file schema
    schema_file = os.path.join(os.path.dirname(__file__), "rtconnect_schema.sql")
    if os.path.exists(schema_file):
        with open(schema_file) as f:
            sql = f.read()
    else:
        print("❌ File rtconnect_schema.sql tidak ditemukan!")
        exit(1)

    conn = psycopg2.connect(DATABASE_URL)
    cur  = conn.cursor()
    
    try:
        cur.execute(sql)
        conn.commit()
        print("✅ Database PostgreSQL berhasil diinisialisasi!")
        print("   Admin : NIK 3201010101010001 / admin123")
        print("   Warga : NIK 3201010101010002 / warga123")
    except Exception as e:
        conn.rollback()
        print(f"⚠️  Info: {e}")
        print("   (Jika error 'already exists', berarti schema sudah ada — itu normal)")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    run()
