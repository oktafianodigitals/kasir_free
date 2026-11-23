"""
utils/helpers.py - Helper functions umum
"""


def parse_currency(text: str) -> int:
    """Parse string currency menjadi integer."""
    try:
        cleaned = text.replace('Rp', '').replace(' ', '').replace('.', '').replace(',', '')
        return int(cleaned) if cleaned else 0
    except (ValueError, AttributeError):
        return 0


def format_rupiah(amount: int) -> str:
    """Format angka menjadi format Rupiah."""
    return f"Rp {amount:,}".replace(',', '.')


def format_perubahan(nilai: int) -> str:
    """Format perubahan stok dengan tanda + / -."""
    if nilai > 0:
        return f"+{nilai}"
    return str(nilai)
