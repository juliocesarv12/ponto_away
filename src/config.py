import os
import re
from dataclasses import dataclass


def only_digits(value: str | None) -> str:
    return re.sub(r"\D", "", value or "")


def parse_ids(value: str | None) -> set[int]:
    if not value or not value.strip():
        return set()
    ids: set[int] = set()
    for part in re.split(r"[,\s]+", value.strip()):
        if part:
            ids.add(int(part))
    return ids


def redact(text: str, secret: str | None) -> str:
    if secret and secret in text:
        return text.replace(secret, "***")
    return text


@dataclass(frozen=True)
class Settings:
    telegram_token: str
    allowed_ids: set[int]
    cpf: str
    senha: str
    matricula: str | None
    portal_url: str
    timezone: str

    def missing(self) -> list[str]:
        missing: list[str] = []
        if not self.telegram_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not self.cpf:
            missing.append("PONTO_CPF")
        if not self.senha:
            missing.append("PONTO_SENHA")
        return missing


def load_settings() -> Settings:
    from dotenv import load_dotenv

    load_dotenv()
    matricula = os.getenv("PONTO_MATRICULA", "").strip()
    return Settings(
        telegram_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        allowed_ids=parse_ids(os.getenv("TELEGRAM_ALLOWED_IDS")),
        cpf=only_digits(os.getenv("PONTO_CPF")),
        senha=os.getenv("PONTO_SENHA", ""),
        matricula=matricula or None,
        portal_url=os.getenv("PONTO_URL", "https://portaldoservidor.sistemas.ro.gov.br/").strip(),
        timezone=os.getenv("TZ", "America/Porto_Velho").strip() or "America/Porto_Velho",
    )
