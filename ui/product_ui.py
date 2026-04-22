"""
ui/product_ui.py - UI Manajemen Produk (Warna, Kategori, Ukuran)
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt

logger = logging.getLogger('product_ui')


class ProductTab(QWidget):
    """Tab manajemen warna, kategori, ukuran."""

    def __init__(self, db, on_changed=None, parent=None):
        super().__init__(parent)
        self.db = db
        # Callback dipanggil setiap kali data produk berubah (add/edit/delete)
        self._on_changed = on_changed
        self._init_ui()
        self.refresh_all()

    def _notify_changed(self):
        """Beritahu controller bahwa data produk telah berubah."""
        if callable(self._on_changed):
            try:
                self._on_changed()
            except Exception as e:
                logger.warning(f"on_changed callback error: {e}")

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        title = QLabel("📦  Manajemen Produk")
        title.setObjectName("section_title")
        root.addWidget(title)

        cols = QHBoxLayout()
        cols.setSpacing(16)

        cols.addWidget(self._build_section(
            "🎨  Warna", "warna_input", "warna_table",
            ["ID", "Nama Warna"], "warna"
        ))
        cols.addWidget(self._build_section(
            "🏷  Kategori", "kategori_input", "kategori_table",
            ["ID", "Nama Kategori"], "kategori"
        ))
        cols.addWidget(self._build_section(
            "📐  Ukuran", "ukuran_input", "ukuran_table",
            ["ID", "Nama Ukuran"], "ukuran"
        ))

        root.addLayout(cols)

    def _build_section(self, title, input_attr, table_attr, headers, item_type):
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        inp = QLineEdit()
        inp.setPlaceholderText(f"Nama {item_type}")
        setattr(self, input_attr, inp)

        btn_row = QHBoxLayout()
        for label, fn in [("➕", lambda _, t=item_type: self._add(t)),
                           ("✏️", lambda _, t=item_type: self._edit(t)),
                           ("🗑", lambda _, t=item_type: self._delete(t))]:
            btn = QPushButton(label)
            if label == "🗑":
                btn.setProperty("class", "danger")
            elif label == "✏️":
                btn.setProperty("class", "secondary")
            btn.clicked.connect(fn)
            btn_row.addWidget(btn)

        tbl = QTableWidget()
        tbl.setColumnCount(2)
        tbl.setHorizontalHeaderLabels(headers)
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        tbl.setAlternatingRowColors(True)
        setattr(self, table_attr, tbl)

        layout.addWidget(inp)
        layout.addLayout(btn_row)
        layout.addWidget(tbl)
        return group

    def refresh_all(self):
        for item_type, getter, table_attr in [
            ('warna', self.db.get_all_warna, 'warna_table'),
            ('kategori', self.db.get_all_kategori, 'kategori_table'),
            ('ukuran', self.db.get_all_ukuran, 'ukuran_table'),
        ]:
            data = getter()
            tbl = getattr(self, table_attr)
            tbl.setRowCount(len(data))
            for i, (id_, nama) in enumerate(data):
                for j, v in enumerate([str(id_), nama]):
                    cell = QTableWidgetItem(v)
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    tbl.setItem(i, j, cell)

    def _add(self, item_type):
        inp = getattr(self, f'{item_type}_input')
        nama = inp.text().strip()
        if not nama:
            QMessageBox.warning(self, "Warning", f"Masukkan nama {item_type}!")
            return
        adder = getattr(self.db, f'add_{item_type}')
        if adder(nama):
            QMessageBox.information(self, "Sukses", f"{item_type.capitalize()} ditambah!")
            inp.clear()
            self.refresh_all()
            self._notify_changed()
        else:
            QMessageBox.warning(self, "Warning", f"{item_type.capitalize()} sudah ada!")

    def _edit(self, item_type):
        tbl = getattr(self, f'{item_type}_table')
        row = tbl.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Warning", f"Pilih {item_type} yang akan diedit!")
            return
        item_id = int(tbl.item(row, 0).text())
        inp = getattr(self, f'{item_type}_input')
        nama_baru = inp.text().strip()
        if not nama_baru:
            QMessageBox.warning(self, "Warning", f"Masukkan nama {item_type} baru!")
            return
        updater = getattr(self.db, f'update_{item_type}')
        if updater(item_id, nama_baru):
            QMessageBox.information(self, "Sukses", f"{item_type.capitalize()} diupdate!")
            inp.clear()
            self.refresh_all()
            self._notify_changed()
        else:
            QMessageBox.warning(self, "Warning", "Nama sudah ada!")

    def _delete(self, item_type):
        tbl = getattr(self, f'{item_type}_table')
        row = tbl.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Warning", f"Pilih {item_type} yang akan dihapus!")
            return
        item_id = int(tbl.item(row, 0).text())
        nama = tbl.item(row, 1).text()
        reply = QMessageBox.question(self, "Konfirmasi", f"Hapus '{nama}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                deleter = getattr(self.db, f'delete_{item_type}')
                deleter(item_id)
                QMessageBox.information(self, "Sukses", f"{item_type.capitalize()} dihapus!")
                self.refresh_all()
                self._notify_changed()
            except ValueError as e:
                QMessageBox.warning(self, "Tidak Dapat Dihapus", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal menghapus {item_type}: {e}")
