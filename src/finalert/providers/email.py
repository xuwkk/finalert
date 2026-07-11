from __future__ import annotations

import smtplib
from email.message import EmailMessage

from finalert.providers.base import Provider


class EmailProvider(Provider):
    def __init__(
        self,
        host: str,
        port: int,
        sender: str,
        recipients: list[str],
        *,
        username: str | None = None,
        password: str | None = None,
        use_ssl: bool = False,
        starttls: bool = True,
        timeout: float = 10.0,
    ) -> None:
        self.host = host
        self.port = port
        self.sender = sender
        self.recipients = recipients
        self.username = username
        self.password = password
        self.use_ssl = use_ssl
        self.starttls = starttls
        self.timeout = timeout

    def send(self, title: str, message: str) -> None:
        email = EmailMessage()
        email["Subject"] = title
        email["From"] = self.sender
        email["To"] = ", ".join(self.recipients)
        email.set_content(message)

        smtp_class = smtplib.SMTP_SSL if self.use_ssl else smtplib.SMTP
        with smtp_class(self.host, self.port, timeout=self.timeout) as smtp:
            if self.starttls and not self.use_ssl:
                smtp.starttls()
            if self.username:
                smtp.login(self.username, self.password or "")
            smtp.send_message(email)

