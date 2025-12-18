import os
import asyncio
from email.message import EmailMessage
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import aiosmtplib
from typing import Optional

from app.core.config import settings

# === Настройки (лучше читать из переменных окружения) ===
SMTP_HOST = settings.SMTP_HOST
SMTP_PORT = int(settings.SMTP_PORT)  # 587 - STARTTLS, 465 - SSL/TLS
SMTP_USERNAME = settings.SMTP_USERNAME
SMTP_PASSWORD = settings.SMTP_PASSWORD  # рекомендую хранить в секретах
FROM_ADDRESS = settings.FROM_ADDRESS
CONFIRMATION_BASE_URL = settings.CONFIRMATION_BASE_URL

# Секрет для подписи токенов (обязательно заменить на безопасный секрет)
TOKEN_SECRET = settings.TOKEN_SECRET
TOKEN_SALT = settings.TOKEN_SALT


# === Генерация / проверка токена ===
def generate_confirmation_token(new_email: str) -> str:
    s = URLSafeTimedSerializer(TOKEN_SECRET)
    return s.dumps(new_email, salt=TOKEN_SALT)


def confirm_token(token: str, expiration: int = 3600) -> Optional[str]:
    """Вернёт адрес email, если токен валиден и не просрочен; иначе None"""
    s = URLSafeTimedSerializer(TOKEN_SECRET)
    try:
        email = s.loads(token, salt=TOKEN_SALT, max_age=expiration)
    except SignatureExpired:
        return None  # токен просрочен
    except BadSignature:
        return None  # неверная подпись / модифицирован
    return email


# === Функция отправки письма (асинхронно) ===
async def send_email_async(
    to_address: str,
    subject: str,
    plain_text: str,
    html_text: Optional[str] = None,
    smtp_host: str = "smtp.timeweb.ru",
    smtp_port: int = 465,
    username: str = SMTP_USERNAME,
    password: str = SMTP_PASSWORD,
    from_address: str = FROM_ADDRESS,
):
    msg = EmailMessage()
    msg["From"] = from_address
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.set_content(plain_text)
    if html_text:
        msg.add_alternative(html_text, subtype="html")

    smtp = aiosmtplib.SMTP(
        hostname=smtp_host,
        port=smtp_port,
        use_tls=True,      # 🔑 ОБЯЗАТЕЛЬНО
        timeout=60,
    )

    await smtp.connect()      # SSL сразу
    await smtp.login(username, password)
    await smtp.send_message(msg)
    await smtp.quit()


# === Утилита: отправить письмо-подтверждение при смене email ===
async def send_confirmation_email_for_change(user_id: str, new_email: str):
    token = generate_confirmation_token(new_email)
    confirm_link = f"{CONFIRMATION_BASE_URL}?token={token}&uid={user_id}"

    subject = "Подтверждение смены адреса электронной почты"
    plain = (
        f"Здравствуйте!\n\n"
        f"Вы запросили смену адреса электронной почты для аккаунта {user_id}.\n"
        f"Чтобы подтвердить смену и окончательно привязать адрес {new_email}, "
        f"перейдите по ссылке:\n\n{confirm_link}\n\n"
        f"Если вы не запрашивали изменение — проигнорируйте это письмо.\n"
    )
    html = f"""
    <html>
      <body>
        <p>Здравствуйте!</p>
        <p>Вы запросили смену адреса электронной почты для аккаунта <b>{user_id}</b>.</p>
        <p>Чтобы подтвердить смену и окончательно привязать адрес <b>{new_email}</b>, нажмите кнопку:</p>
        <p><a href="{confirm_link}" style="display:inline-block;padding:10px 16px;border-radius:6px;text-decoration:none;border:1px solid #007BFF;">Подтвердить адрес</a></p>
        <p>Если вы не запрашивали изменение — проигнорируйте это письмо.</p>
      </body>
    </html>
    """
    await send_email_async(
        to_address=new_email,
        subject=subject,
        plain_text=plain,
        html_text=html,
    )
