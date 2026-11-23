"""
ui/table_utils.py - Helper tabel terpusat
Memastikan tinggi baris cukup untuk badge status & tombol aksi,
sehingga teks tidak terpotong.
"""

from PyQt6.QtWidgets import (
    QTableWidget, QHeaderView, QWidget, QHBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFontMetrics

ROW_HEIGHT = 46        # tinggi baris data (px)
HEADER_HEIGHT = 40     # tinggi header kolom (px)
BADGE_HEIGHT = 26      # tinggi badge status (px)
BADGE_MIN_WIDTH = 72   # lebar minimum badge (px)
BTN_W, BTN_H = 36, 32  # ukuran tombol aksi dalam tabel (px)


def setup_table(tbl: QTableWidget, row_height: int = ROW_HEIGHT) -> QTableWidget:
    """Terapkan tinggi baris tetap & header yang lega pada sebuah tabel."""
    vh = tbl.verticalHeader()
    vh.setMinimumSectionSize(row_height)
    vh.setDefaultSectionSize(row_height)
    vh.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
    tbl.horizontalHeader().setFixedHeight(HEADER_HEIGHT)
    tbl.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
    return tbl


def _wrap(widget: QWidget, spacing: int = 0) -> QWidget:
    """Bungkus widget agar rata tengah di dalam sel & latar transparan."""
    box = QWidget()
    box.setObjectName("cell_wrap")
    box.setStyleSheet("QWidget#cell_wrap { background: transparent; }")
    lay = QHBoxLayout(box)
    lay.setContentsMargins(6, 0, 6, 0)
    lay.setSpacing(spacing)
    lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lay.addWidget(widget, 0, Qt.AlignmentFlag.AlignCenter)
    return box


def make_badge(text: str, style: str) -> QWidget:
    """Badge status (LUNAS, MENIPIS, dst) yang tidak terpotong."""
    lbl = QLabel(text)
    lbl.setStyleSheet(style)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lbl.setFixedHeight(BADGE_HEIGHT)
    # Lebar badge dihitung dari teksnya (font tebal 11px + padding kiri/kanan)
    font = lbl.font()
    font.setBold(True)
    font.setPixelSize(11)
    text_w = QFontMetrics(font).horizontalAdvance(text)
    lbl.setFixedWidth(max(BADGE_MIN_WIDTH, text_w + 26))
    return _wrap(lbl)


def make_table_button(text: str, style: str, tooltip: str = "") -> QPushButton:
    """Tombol aksi berukuran tetap untuk dipakai di dalam sel tabel."""
    btn = QPushButton(text)
    btn.setStyleSheet(style)
    btn.setFixedSize(BTN_W, BTN_H)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    if tooltip:
        btn.setToolTip(tooltip)
    return btn


def make_button_group(buttons, spacing: int = 6) -> QWidget:
    """Susun beberapa tombol aksi horizontal, rata tengah dalam sel."""
    box = QWidget()
    box.setObjectName("cell_wrap")
    box.setStyleSheet("QWidget#cell_wrap { background: transparent; }")
    lay = QHBoxLayout(box)
    lay.setContentsMargins(6, 0, 6, 0)
    lay.setSpacing(spacing)
    lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
    for b in buttons:
        lay.addWidget(b, 0, Qt.AlignmentFlag.AlignCenter)
    return box
