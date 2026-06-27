from __future__ import annotations


DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def validate_base(base: int) -> None:
    if base < 2 or base > len(DIGITS):
        raise ValueError("codex/base must be between 2 and 36")


def text_to_ascii_bytes(text: str) -> list[int]:
    return list(text.encode("utf-8"))


def bytes_to_text(values: list[int]) -> str:
    return bytes(values).decode("utf-8")


def decimal_to_base(value: int, base: int) -> str:
    validate_base(base)
    if value < 0:
        raise ValueError("negative values are not supported")
    if value == 0:
        return "0"

    digits: list[str] = []
    current = value
    while current:
        current, remainder = divmod(current, base)
        digits.append(DIGITS[remainder])
    return "".join(reversed(digits))

