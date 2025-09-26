import os, base64, asyncio
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


# --- derive_key ---
async def derive_key(password: str, salt: bytes) -> bytes:
    """Асинхронная генерация AES-ключа из пароля"""

    def _derive():
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # AES-256
            salt=salt,
            iterations=200_000,  # чем больше, тем надёжнее
            backend=default_backend()
        )
        return kdf.derive(password.encode())

    return await asyncio.to_thread(_derive)


# --- encrypt ---
async def encrypt(plaintext: str, password: str) -> str:
    salt = os.urandom(16)
    key = await derive_key(password, salt)
    iv = os.urandom(12)

    def _encrypt():
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext.encode()) + encryptor.finalize()
        return base64.b64encode(salt + iv + encryptor.tag + ciphertext).decode()

    return await asyncio.to_thread(_encrypt)


# --- decrypt ---
async def decrypt(ciphertext_b64: str, password: str) -> str:
    raw = base64.b64decode(ciphertext_b64)
    salt, iv, tag, ciphertext = raw[:16], raw[16:28], raw[28:44], raw[44:]

    key = await derive_key(password, salt)

    def _decrypt():
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext.decode()

    return await asyncio.to_thread(_decrypt)
