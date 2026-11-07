# -*- coding: utf-8 -*-
"""
Hash de senhas dos usuários com PBKDF2-SHA256 + salt (biblioteca padrão do Python).

Formato salvo em users.password_hash:
    pbkdf2_sha256$<iterações>$<salt hex>$<hash hex>

Hashes antigos (SHA-256 puro, 64 caracteres hex, sem salt) ainda são aceitos
no login e convertidos para o formato novo automaticamente — veja login.py.
"""

import hashlib
import hmac
import secrets

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000


def hash_password(password: str) -> str:
    """Gera o hash seguro de uma senha nova."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"{ALGORITHM}${ITERATIONS}${salt.hex()}${digest.hex()}"


def _is_legacy_sha256(stored: str) -> bool:
    return len(stored) == 64 and all(c in "0123456789abcdef" for c in stored.lower())


def verify_password(password: str, stored: str | None) -> bool:
    """Confere a senha digitada contra o hash salvo (formato novo ou antigo)."""
    if not stored:
        return False

    if stored.startswith(ALGORITHM + "$"):
        try:
            _, iterations, salt_hex, digest_hex = stored.split("$")
            digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                                         bytes.fromhex(salt_hex), int(iterations))
        except ValueError:
            return False
        return hmac.compare_digest(digest.hex(), digest_hex)

    if _is_legacy_sha256(stored):
        legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy, stored.lower())

    return False


def needs_upgrade(stored: str | None) -> bool:
    """True se o hash está no formato antigo ou com menos iterações que o atual."""
    if not stored or not stored.startswith(ALGORITHM + "$"):
        return True
    try:
        return int(stored.split("$")[1]) < ITERATIONS
    except (IndexError, ValueError):
        return True
