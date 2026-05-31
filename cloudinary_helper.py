"""
RTConnect - Cloudinary Helper
Upload file ke Cloudinary, return secure_url
Jika CLOUDINARY_URL tidak diset, simpan file lokal sebagai fallback.
"""
import os

CLOUDINARY_URL = os.environ.get("CLOUDINARY_URL", "")
ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp", "pdf"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

def upload_file(file_storage, folder: str, public_id_prefix: str = "") -> str:
    """
    Upload file. Jika Cloudinary dikonfigurasi, upload ke sana.
    Jika tidak, simpan lokal di folder uploads/ dan kembalikan path.
    """
    if CLOUDINARY_URL and not CLOUDINARY_URL.startswith("cloudinary://123"):
        try:
            import cloudinary
            import cloudinary.uploader
            cloudinary.config(cloudinary_url=CLOUDINARY_URL)
            result = cloudinary.uploader.upload(
                file_storage,
                folder=f"rtconnect/{folder}",
                public_id=public_id_prefix if public_id_prefix else None,
                overwrite=True,
                resource_type="auto",
            )
            return result["secure_url"]
        except Exception as e:
            raise Exception(f"Cloudinary error: {e}")

    # Fallback: simpan lokal
    upload_dir = os.path.join(os.path.dirname(__file__), "uploads", folder)
    os.makedirs(upload_dir, exist_ok=True)

    filename = file_storage.filename
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    save_name = f"{public_id_prefix or 'file'}.{ext}"
    save_path = os.path.join(upload_dir, save_name)

    file_storage.save(save_path)
    return f"/uploads/{folder}/{save_name}"
