"""Creates backend/.env with fresh random secrets. Usage: python generate_env.py [GEMINI_API_KEY]"""
import secrets, sys, pathlib
from cryptography.fernet import Fernet

path = pathlib.Path(__file__).parent / ".env"
if path.exists():
    sys.exit(f"{path} already exists - delete it first if you want to regenerate.")
gemini = sys.argv[1] if len(sys.argv) > 1 else ""
path.write_text(
    f"JWT_SECRET_KEY={secrets.token_urlsafe(48)}\n"
    f"FERNET_KEY={Fernet.generate_key().decode()}\n"
    f"GEMINI_API_KEY={gemini}\n"
    "FALKORDB_HOST=localhost\nFALKORDB_PORT=6379\nFALKORDB_PASSWORD=\n"
    "MONGODB_URL=mongodb://localhost:27017\nDATABASE_NAME=healthcare_optimization\n"
)
print(f"Wrote {path}")
