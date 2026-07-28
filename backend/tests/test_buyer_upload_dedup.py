"""Tests for buyer upload duplicate filtering."""

from app.acquisition.buyer_upload import _partition_new_purchases, build_source_row_key


def test_source_row_key_allows_repeat_buyer_same_sku_state():
    row_a = {
        "email": "buyer@example.com",
        "sku_token": "V4",
        "product_raw": "Master V4",
        "state": "CA",
        "order_ref": "",
        "paid_at": "",
        "row_number": 10,
        "source_channel": "legacy",
    }
    row_b = {**row_a, "row_number": 11}
    assert build_source_row_key(row_a) != build_source_row_key(row_b)


def test_source_row_key_matches_reuploaded_row():
    row = {
        "email": "buyer@example.com",
        "sku_token": "V4",
        "product_raw": "Master V4",
        "state": "CA",
        "order_ref": "ORD-1001",
        "paid_at": "2025-03-01",
        "row_number": 10,
        "source_channel": "shopify",
    }
    assert build_source_row_key(row) == build_source_row_key(dict(row))


class _FakeQuery:
    def __init__(self, keys):
        self._keys = keys

    def filter(self, *_args, **_kwargs):
        return self

    def all(self):
        return [(key,) for key in self._keys]


class _FakeSession:
    def __init__(self, keys):
        self._keys = keys

    def query(self, *_args, **_kwargs):
        return _FakeQuery(self._keys)


def test_partition_new_purchases_keeps_repeat_buyer_rows():
    existing = build_source_row_key(
        {
            "email": "existing@example.com",
            "sku_token": "V4",
            "product_raw": "Master V4",
            "state": "CA",
            "order_ref": "",
            "paid_at": "",
            "row_number": 2,
            "source_channel": "legacy",
        }
    )
    db = _FakeSession([existing])
    parsed = [
        {
            "email": "existing@example.com",
            "sku_token": "V4",
            "product_raw": "Master V4",
            "state": "CA",
            "order_ref": "",
            "paid_at": "",
            "row_number": 2,
            "source_channel": "legacy",
        },
        {
            "email": "existing@example.com",
            "sku_token": "V4",
            "product_raw": "Master V4",
            "state": "CA",
            "order_ref": "",
            "paid_at": "",
            "row_number": 99,
            "source_channel": "legacy",
        },
    ]

    new_rows, skipped = _partition_new_purchases(db, parsed)

    assert skipped == 1
    assert len(new_rows) == 1
    assert new_rows[0]["row_number"] == 99
