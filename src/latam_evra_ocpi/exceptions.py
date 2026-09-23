"""Excepciones del SDK."""

from __future__ import annotations


class OcpiError(Exception):
    """Error reportado por el Hub dentro del sobre OCPI.

    El Hub siempre responde HTTP 200/4xx/5xx según corresponda, pero el
    contrato OCPI espera que el llamador revise el campo ``status_code``
    dentro del cuerpo de la respuesta (1000 = éxito; 2000-3999 = error).
    Esta excepción se lanza cuando ``status_code`` indica un error, y expone
    ese código y el ``status_message`` asociado para que el llamador pueda
    manejarlo programáticamente.
    """

    def __init__(
        self,
        status_code: int,
        status_message: str,
        *,
        http_status: int | None = None,
    ) -> None:
        self.status_code = status_code
        self.status_message = status_message
        self.http_status = http_status
        super().__init__(f"OCPI error {status_code}: {status_message}")

    def __repr__(self) -> str:  # pragma: no cover - cosmético
        return (
            f"OcpiError(status_code={self.status_code!r}, "
            f"status_message={self.status_message!r}, "
            f"http_status={self.http_status!r})"
        )
