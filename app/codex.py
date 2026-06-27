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


def base_to_decimal(value_str: str, base: int) -> int:
    validate_base(base)
    value = 0
    for char in value_str.upper():
        digit = DIGITS.find(char)
        if digit < 0 or digit >= base:
            raise ValueError(f"invalid digit {char!r} for base {base}")
        value = value * base + digit
    return value


def encode_payload_for_codex(values: list[int], codex: int) -> list[str]:
    return [decimal_to_base(value, codex) for value in values]


def decode_payload_from_codex(encoded_values: list[str], codex: int) -> list[int]:
    decoded = [base_to_decimal(value, codex) for value in encoded_values]
    for value in decoded:
        if value < 0 or value > 255:
            raise ValueError(f"decoded value {value} is not a byte")
    return decoded
