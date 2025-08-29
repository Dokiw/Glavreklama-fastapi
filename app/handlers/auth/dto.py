from dataclasses import dataclass
from typing import Optional

@dataclass
class UserAuthData:
    id: int
    pass_hash: str
    user_name: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    def verify_password(self, plaintext: str) -> Optional[bool]:
        if not self.pass_hash:
            return None  # если хеша нет, возвращаем None
        from passlib.hash import bcrypt
        return bcrypt.verify(plaintext, self.pass_hash)