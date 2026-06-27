from app.codex import (
    base_to_decimal,
    bytes_to_text,
    decimal_to_base,
    decode_payload_from_codex,
    encode_payload_for_codex,
    text_to_ascii_bytes,
)


def test_base_conversion_examples():
    assert decimal_to_base(72, 5) == "242"
    assert decimal_to_base(72, 14) == "52"
    assert decimal_to_base(119, 14) == "87"
    assert base_to_decimal("7A", 14) == 108


def test_payload_roundtrip():
    values = text_to_ascii_bytes("Hello world")
    encoded = encode_payload_for_codex(values, 14)
    decoded = decode_payload_from_codex(encoded, 14)
    assert bytes_to_text(decoded) == "Hello world"
