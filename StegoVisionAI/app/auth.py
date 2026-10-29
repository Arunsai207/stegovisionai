import base64, hashlib, hmac, json, os, time
from fastapi import HTTPException, Request

APP_SECRET = os.getenv("APP_SECRET", "development-only-change-me-please")

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 240_000)
    return _b64(salt), _b64(digest)

def verify_password(password: str, salt_text: str, expected: str) -> bool:
    salt = _unb64(salt_text)
    _, actual = hash_password(password, salt)
    return hmac.compare_digest(actual, expected)

def create_token(user_id: int, email: str) -> str:
    payload = {"sub": user_id, "email": email, "exp": int(time.time()) + 60 * 60 * 12}
    body = _b64(json.dumps(payload, separators=(",", ":")).encode())
    signature = _b64(hmac.new(APP_SECRET.encode(), body.encode(), hashlib.sha256).digest())
    return body + "." + signature

def read_token(token: str) -> dict:
    try:
        body, signature = token.split(".", 1)
        expected = _b64(hmac.new(APP_SECRET.encode(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("invalid signature")
        payload = json.loads(_unb64(body))
        if int(payload["exp"]) < int(time.time()):
            raise ValueError("expired")
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Session expired. Please sign in again.")

def current_user(request: Request) -> dict:
    auth = request.headers.get("authorization", "")
    token = auth[7:] if auth.lower().startswith("bearer ") else request.cookies.get("sv_session")
    if not token:
        raise HTTPException(status_code=401, detail="Please sign in to continue.")
    return read_token(token)
