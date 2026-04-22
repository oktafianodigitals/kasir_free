"""
ui/transaction_ui.py - UI Transaksi (Tab Transaksi & Detail Transaksi)
"""

import logging
import traceback
import os
import sys
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFormLayout, QGroupBox, QLineEdit,
    QDialog, QDialogButtonBox, QDateEdit, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QDate
from ui.styles import BADGE_LUNAS, BADGE_BELUM, TABLE_BTN_VIEW, TABLE_BTN_EDIT, TABLE_BTN_PRINT
from utils.helpers import parse_currency, format_rupiah

logger = logging.getLogger('transaction_ui')


def open_pdf(filepath):
    """Buka file PDF menggunakan aplikasi default sistem."""
    try:
        if sys.platform.startswith('win'):
            os.startfile(filepath)
        elif sys.platform.startswith('darwin'):
            subprocess.Popen(['open', filepath])
        else:
            subprocess.Popen(['xdg-open', filepath])
        return True
    except Exception as e:
        logger.error(f"Gagal membuka PDF: {e}")
        return False


class TransactionTab(QWidget):
    """Tab Transaksi - form kasir, keranjang, checkout."""

    def __init__(self, db, invoice_gen, parent=None):
        super().__init__(parent)
        self.db = db
        self.invoice_gen = invoice_gen
        self.cart_items = []
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        title = QLabel("🛒  Transaksi Penjualan")
        title.setObjectName("section_title")
        root.addWidget(title)

        body = QHBoxLayout()
        body.setSpacing(16)

        # ── Kiri: Form Input ──
        left = QVBoxLayout()

        form_group = QGroupBox("Form Item")
        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        self.nama_pembeli = QLineEdit()
        self.nama_pembeli.setPlaceholderText("Masukkan nama pembeli")

        self.combo_warna = QComboBox()
        self.combo_kategori = QComboBox()
        self.combo_ukuran = QComboBox()

        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 999)

        self.harga_edit = QLineEdit()
        self.harga_edit.setPlaceholderText("Harga satuan (Rp)")

        self.pembayaran_edit = QLineEdit()
        self.pembayaran_edit.setPlaceholderText("Jumlah pembayaran (Rp)")
        self.pembayaran_edit.textChanged.connect(self._on_pembayaran_changed)

        form_layout.addRow("Nama Pembeli:", self.nama_pembeli)
        form_layout.addRow("Warna:", self.combo_warna)
        form_layout.addRow("Kategori:", self.combo_kategori)
        form_layout.addRow("Ukuran:", self.combo_ukuran)
        form_layout.addRow("Qty:", self.qty_spin)
        form_layout.addRow("Harga (Rp):", self.harga_edit)
        form_layout.addRow("Pembayaran (Rp):", self.pembayaran_edit)
        form_group.setLayout(form_layout)

        btn_row = QHBoxLayout()
        btn_tambah = QPushButton("➕  Tambah ke Keranjang")
        btn_tambah.clicked.connect(self._tambah_ke_keranjang)
        btn_checkout = QPushButton("✅  Checkout")
        btn_checkout.setProperty("class", "success")
        btn_checkout.clicked.connect(self._checkout)
        btn_clear = QPushButton("🗑  Clear")
        btn_clear.setProperty("class", "danger")
        btn_clear.clicked.connect(self._clear_keranjang)
        btn_row.addWidget(btn_tambah)
        btn_row.addWidget(btn_checkout)
        btn_row.addWidget(btn_clear)

        left.addWidget(form_group)
        left.addLayout(btn_row)
        left.addStretch()

        # ── Kanan: Keranjang ──
        right = QVBoxLayout()
        cart_group = QGroupBox("Keranjang Belanja")
        cart_layout = QVBoxLayout(cart_group)

        self.keranjang_table = QTableWidget()
        self.keranjang_table.setColumnCount(7)
        self.keranjang_table.setHorizontalHeaderLabels([
            "Warna", "Kategori", "Ukuran", "Qty", "Harga", "Total", ""
        ])
        self.keranjang_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Info Panel untuk stok
        self.stok_info_panel = QFrame()
        self.stok_info_panel.setObjectName("stok_info_panel")
        self.stok_info_panel.setStyleSheet("""
            QFrame#stok_info_panel {
                background-color: #313244;
                border-radius: 8px;
                padding: 10px;
                border: 1px solid #45475a;
            }
        """)
        stok_layout = QVBoxLayout(self.stok_info_panel)
        stok_layout.setContentsMargins(12, 10, 12, 10)
        self.stok_info_label = QLabel("📦 Stok tersedia akan ditampilkan di sini")
        self.stok_info_label.setStyleSheet("color: #a6adc8; font-size: 11px;")
        stok_layout.addWidget(self.stok_info_label)
        cart_layout.addWidget(self.stok_info_panel)

        self.total_label = QLabel("Total: Rp 0")
        self.total_label.setObjectName("total_label")

        # Panel untuk kembalian/sisa
        self.kembalian_frame = QFrame()
        self.kembalian_frame.setStyleSheet("background-color: #24273a; border-radius: 6px;")
        kembalian_layout = QHBoxLayout(self.kembalian_frame)
        kembalian_layout.setContentsMargins(12, 8, 12, 8)
        self.kembalian_label = QLabel("Kembalian: Rp 0")
        self.kembalian_label.setStyleSheet("color: #a6e3a1; font-size: 14px; font-weight: bold;")
        self.sisa_label = QLabel("Sisa: Rp 0")
        self.sisa_label.setStyleSheet("color: #f38ba8; font-size: 14px; font-weight: bold;")
        self.sisa_label.setVisible(False)
        kembalian_layout.addWidget(self.kembalian_label)
        kembalian_layout.addStretch()
        kembalian_layout.addWidget(self.sisa_label)

        cart_layout.addWidget(self.keranjang_table)
        cart_layout.addWidget(self.total_label)
        cart_layout.addWidget(self.kembalian_frame)
        right.addWidget(cart_group)

        body.addLayout(left, 4)
        body.addLayout(right, 6)
        root.addLayout(body)

    def load_combo_data(self):
        for combo, getter in [
            (self.combo_warna, self.db.get_all_warna),
            (self.combo_kategori, self.db.get_all_kategori),
            (self.combo_ukuran, self.db.get_all_ukuran),
        ]:
            combo.clear()
            for row in getter():
                combo.addItem(row[1], row[0])

    def refresh(self):
        """Dipanggil saat navigasi ke tab ini agar combo selalu sinkron dengan data terbaru."""
        self.load_combo_data()
        self._update_stok_info()

    def _update_stok_info(self):
        """Update info stok berdasarkan item di keranjang."""
        if not self.cart_items:
            self.stok_info_label.setText("📦 Stok tersedia akan ditampilkan di sini")
            self.stok_info_label.setStyleSheet("color: #a6adc8; font-size: 11px;")
            return
        try:
            from db_gudang import DatabaseGudang
            db_gudang = DatabaseGudang()
            info_lines = ["📦 Stok Saat Ini:"]
            for item in self.cart_items:
                stok = db_gudang.get_stok_by_combo(item['warna_id'], item['kategori_id'], item['ukuran_id'])
                stok_jumlah = stok['jumlah'] if stok else 0
                item_name = f"{item['kategori_nama']} / {item['warna_nama']} / {item['ukuran_nama']}"
                qty_dibeli = item['qty']
                stok_setelah = max(0, stok_jumlah - qty_dibeli)
                if stok_jumlah == 0:
                    info_lines.append(f"  • {item_name}: <span style='color: #f38ba8;'>STOK HABIS</span>")
                elif stok_jumlah < qty_dibeli:
                    info_lines.append(f"  • {item_name}: <span style='color: #f9e2af;'>Stok {stok_jumlah} (kurang!)</span>")
                else:
                    info_lines.append(f"  • {item_name}: <span style='color: #a6e3a1;'>{stok_jumlah}</span> → {stok_setelah}")
            self.stok_info_label.setText("<br>".join(info_lines))
        except Exception as e:
            self.stok_info_label.setText(f"📦 Tidak dapat memuat info stok: {e}")

    def _on_pembayaran_changed(self):
        """Update kembalian/sisa saat pembayaran berubah."""
        try:
            total = sum(i['qty'] * i['harga'] for i in self.cart_items)
            pembayaran = parse_currency(self.pembayaran_edit.text())
            selisih = pembayaran - total
            if selisih >= 0:
                self.kembalian_label.setText(f"Kembalian: {format_rupiah(selisih)}")
                self.kembalian_label.setStyleSheet("color: #a6e3a1; font-size: 14px; font-weight: bold;")
                self.sisa_label.setVisible(False)
            else:
                self.kembalian_label.setText("Kembalian: Rp 0")
                self.sisa_label.setText(f"Sisa: {format_rupiah(abs(selisih))}")
                self.sisa_label.setVisible(True)
        except Exception:
            self.kembalian_label.setText("Kembalian: Rp 0")
            self.sisa_label.setVisible(False)

    def _tambah_ke_keranjang(self):
        try:
            if not self.combo_warna.currentData():
                QMessageBox.warning(self, "Warning", "Pilih warna!")
                return
            harga = parse_currency(self.harga_edit.text())
            if harga <= 0:
                QMessageBox.warning(self, "Warning", "Masukkan harga yang valid!")
                return
            self.cart_items.append({
                'warna_id': self.combo_warna.currentData(),
                'warna_nama': self.combo_warna.currentText(),
                'kategori_id': self.combo_kategori.currentData(),
                'kategori_nama': self.combo_kategori.currentText(),
                'ukuran_id': self.combo_ukuran.currentData(),
                'ukuran_nama': self.combo_ukuran.currentText(),
                'qty': self.qty_spin.value(),
                'harga': harga,
            })
            self._update_keranjang_table()
            self._update_stok_info()
            self._on_pembayaran_changed()
            self.harga_edit.clear()
            self.qty_spin.setValue(1)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _update_keranjang_table(self):
        self.keranjang_table.setRowCount(len(self.cart_items))
        total = 0
        for row, item in enumerate(self.cart_items):
            item_total = item['qty'] * item['harga']
            total += item_total
            for col, val in enumerate([
                item['warna_nama'], item['kategori_nama'], item['ukuran_nama'],
                str(item['qty']), format_rupiah(item['harga']),
                format_rupiah(item_total)
            ]):
                cell = QTableWidgetItem(val)
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.keranjang_table.setItem(row, col, cell)
            btn = QPushButton("✕")
            btn.setProperty("class", "danger")
            btn.setFixedWidth(40)
            btn.clicked.connect(lambda _, idx=row: self._remove_item(idx))
            self.keranjang_table.setCellWidget(row, 6, btn)
        self.total_label.setText(f"Total: {format_rupiah(total)}")

    def _remove_item(self, index):
        if 0 <= index < len(self.cart_items):
            self.cart_items.pop(index)
            self._update_keranjang_table()
            self._update_stok_info()
            self._on_pembayaran_changed()

    def _clear_keranjang(self):
        reply = QMessageBox.question(self, "Konfirmasi", "Hapus semua item keranjang?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.cart_items.clear()
            self._update_keranjang_table()
            self._update_stok_info()
            self._on_pembayaran_changed()

    def _checkout(self):
        try:
            if not self.cart_items:
                QMessageBox.warning(self, "Warning", "Keranjang kosong!")
                return
            nama = self.nama_pembeli.text().strip()
            if not nama:
                QMessageBox.warning(self, "Warning", "Masukkan nama pembeli!")
                return
            pembayaran = parse_currency(self.pembayaran_edit.text())
            if pembayaran < 0:
                QMessageBox.warning(self, "Warning", "Pembayaran tidak boleh negatif!")
                return
            subtotal = sum(i['qty'] * i['harga'] for i in self.cart_items)

            # Konfirmasi jika pembayaran belum lunas
            if pembayaran == 0:
                reply = QMessageBox.question(
                    self, "Konfirmasi",
                    "Pembayaran Rp 0. Transaksi akan disimpan sebagai BELUM LUNAS.\nLanjutkan?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            elif pembayaran < subtotal:
                reply = QMessageBox.question(
                    self, "Konfirmasi",
                    f"Pembayaran {format_rupiah(pembayaran)} kurang dari subtotal {format_rupiah(subtotal)}.\n"
                    f"Kekurangan: {format_rupiah(subtotal - pembayaran)}\n"
                    f"Transaksi akan disimpan sebagai BELUM LUNAS.\nLanjutkan?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

            detail_items = [{
                'warna_id': i['warna_id'],
                'kategori_id': i['kategori_id'],
                'ukuran_id': i['ukuran_id'],
                'qty': i['qty'],
                'harga': i['harga'],
            } for i in self.cart_items]

            result = self.db.add_transaksi(nama, subtotal, pembayaran, detail_items)
            filepath = self.invoice_gen.print_invoice(result['transaksi_id'])

            # Bersihkan form
            self.nama_pembeli.clear()
            self.pembayaran_edit.clear()
            self.cart_items.clear()
            self._update_keranjang_table()
            self._update_stok_info()
            self._on_pembayaran_changed()

            # Tampilkan popup sukses + opsi print invoice
            self._show_checkout_success_dialog(result, filepath)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error checkout: {e}")
            logger.error(traceback.format_exc())

    def _show_checkout_success_dialog(self, result, filepath):
        """Tampilkan dialog sukses checkout dengan opsi cetak invoice."""
        dialog = QDialog(self)
        dialog.setWindowTitle("✅  Transaksi Berhasil")
        dialog.setFixedSize(420, 280)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        # Icon & judul
        lbl_icon = QLabel("✅")
        lbl_icon.setStyleSheet("font-size: 36px;")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_icon)

        lbl_title = QLabel("Transaksi Berhasil!")
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #a6e3a1;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)

        # Info transaksi
        info_frame = QFrame()
        info_frame.setStyleSheet(
            "QFrame { background-color: #313244; border-radius: 8px; }"
        )
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(14, 12, 14, 12)
        info_layout.setSpacing(5)

        lbl_invoice = QLabel(f"📄  No. Invoice: <b>{result['no_invoice']}</b>")
        lbl_invoice.setStyleSheet("color: #cdd6f4; font-size: 12px;")
        color_status = '#a6e3a1' if result['status'] == 'LUNAS' else '#f9e2af'
        lbl_status = QLabel(f"📌  Status: <b><span style='color:{color_status};'>{result['status']}</span></b>")
        lbl_status.setStyleSheet("font-size: 12px; color: #cdd6f4;")
        lbl_status.setTextFormat(Qt.TextFormat.RichText)

        info_layout.addWidget(lbl_invoice)
        info_layout.addWidget(lbl_status)

        if filepath:
            lbl_file = QLabel("📁  File invoice PDF telah tersimpan")
            lbl_file.setStyleSheet("color: #89b4fa; font-size: 11px;")
            info_layout.addWidget(lbl_file)

        layout.addWidget(info_frame)

        # Tombol aksi
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        btn_close = QPushButton("Tutup")
        btn_close.setProperty("class", "secondary")
        btn_close.clicked.connect(dialog.accept)

        btn_print = QPushButton("🖨  Cetak / Buka Invoice")
        btn_print.setProperty("class", "success")

        if filepath:
            def do_print():
                if not open_pdf(filepath):
                    QMessageBox.warning(dialog, "Gagal", "Tidak dapat membuka file PDF.\nBuka secara manual dari folder invoice/")
                dialog.accept()
            btn_print.clicked.connect(do_print)
        else:
            btn_print.setEnabled(False)
            btn_print.setToolTip("Invoice tidak tersedia")

        btn_layout.addWidget(btn_close)
        btn_layout.addWidget(btn_print)
        layout.addLayout(btn_layout)

        dialog.exec()

class DetailTransaksiTab(QWidget):
    """Tab Detail Transaksi - riwayat, filter tanggal, export."""

    def __init__(self, db, invoice_gen, excel_export, parent=None):
        super().__init__(parent)
        self.db = db
        self.invoice_gen = invoice_gen
        self.excel_export = excel_export
        self._all_data = []  # cache semua data untuk pencarian lokal
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        title = QLabel("📊  Riwayat Transaksi")
        title.setObjectName("section_title")
        root.addWidget(title)

        # ── Baris 1: Filter Tanggal ──
        ctrl = QHBoxLayout()
        self.date_from = QDateEdit(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        self.date_to = QDateEdit(QDate.currentDate())
        self.date_to.setCalendarPopup(True)

        btn_filter = QPushButton("🔍  Filter Tanggal")
        btn_filter.clicked.connect(self._filter_date)
        btn_refresh = QPushButton("🔄  Refresh")
        btn_refresh.setProperty("class", "secondary")
        btn_refresh.clicked.connect(self.load_data)
        btn_export = QPushButton("📤  Export Excel")
        btn_export.setProperty("class", "success")
        btn_export.clicked.connect(self._export)

        ctrl.addWidget(QLabel("Dari:"))
        ctrl.addWidget(self.date_from)
        ctrl.addWidget(QLabel("Sampai:"))
        ctrl.addWidget(self.date_to)
        ctrl.addWidget(btn_filter)
        ctrl.addStretch()
        ctrl.addWidget(btn_refresh)
        ctrl.addWidget(btn_export)
        root.addLayout(ctrl)

        # ── Baris 2: Search Bar ──
        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        lbl_search = QLabel("🔎")
        lbl_search.setStyleSheet("font-size: 14px;")
        search_row.addWidget(lbl_search)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Cari berdasarkan nama, ID, no invoice...")
        self.search_edit.setMinimumWidth(260)
        self.search_edit.textChanged.connect(self._apply_search)
        search_row.addWidget(self.search_edit, 3)

        lbl_status = QLabel("Status:")
        lbl_status.setStyleSheet("color: #a6adc8;")
        search_row.addWidget(lbl_status)

        self.combo_status = QComboBox()
        self.combo_status.addItems(["Semua", "LUNAS", "BELUM LUNAS"])
        self.combo_status.setFixedWidth(130)
        self.combo_status.currentIndexChanged.connect(self._apply_search)
        search_row.addWidget(self.combo_status)

        lbl_tgl = QLabel("Tgl Cari:")
        lbl_tgl.setStyleSheet("color: #a6adc8;")
        search_row.addWidget(lbl_tgl)

        self.search_date = QLineEdit()
        self.search_date.setPlaceholderText("yyyy-mm-dd atau kosong")
        self.search_date.setFixedWidth(130)
        self.search_date.textChanged.connect(self._apply_search)
        search_row.addWidget(self.search_date)

        btn_clear_search = QPushButton("✕ Clear")
        btn_clear_search.setProperty("class", "secondary")
        btn_clear_search.setFixedWidth(80)
        btn_clear_search.clicked.connect(self._clear_search)
        search_row.addWidget(btn_clear_search)

        self.lbl_result_count = QLabel("Menampilkan: 0 data")
        self.lbl_result_count.setStyleSheet("color: #6c7086; font-size: 10px;")
        search_row.addWidget(self.lbl_result_count)

        root.addLayout(search_row)

        self.tbl = QTableWidget()
        self.tbl.setColumnCount(8)
        self.tbl.setHorizontalHeaderLabels([
            "ID", "Invoice", "Nama Pembeli", "Tanggal",
            "Subtotal", "Pembayaran", "Status", "Aksi"
        ])
        hdr = self.tbl.horizontalHeader()
        hdr.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tbl.setAlternatingRowColors(True)
        root.addWidget(self.tbl)

    def load_data(self):
        self._all_data = [tuple(row) for row in self.db.get_all_transaksi()]
        self._apply_search()

    def _filter_date(self):
        start = self.date_from.date().toString("yyyy-MM-dd")
        end = self.date_to.date().toString("yyyy-MM-dd")
        try:
            conn = self.db.get_connection()
            conn.row_factory = __import__('sqlite3').Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nama_pembeli, subtotal, pembayaran, status, tanggal, no_invoice
                FROM transaksi WHERE tanggal BETWEEN ? AND ?
                ORDER BY id DESC
            ''', (start, end))
            data = cursor.fetchall()
            conn.close()
            self._all_data = [tuple(row) for row in data]
            self._apply_search()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _clear_search(self):
        """Reset semua filter pencarian."""
        self.search_edit.blockSignals(True)
        self.search_date.blockSignals(True)
        self.combo_status.blockSignals(True)
        self.search_edit.clear()
        self.search_date.clear()
        self.combo_status.setCurrentIndex(0)
        self.search_edit.blockSignals(False)
        self.search_date.blockSignals(False)
        self.combo_status.blockSignals(False)
        self._apply_search()

    def _apply_search(self):
        """Filter tabel berdasarkan keyword, status, dan tanggal."""
        keyword = self.search_edit.text().strip().lower()
        status_filter = self.combo_status.currentText()
        date_filter = self.search_date.text().strip()

        filtered = []
        for trx in self._all_data:
            id_, nama, subtotal, pembayaran, status, tanggal, no_invoice = trx

            # Filter keyword: nama, id, no_invoice
            if keyword:
                match = (
                    keyword in str(id_).lower() or
                    keyword in nama.lower() or
                    keyword in no_invoice.lower()
                )
                if not match:
                    continue

            # Filter status
            if status_filter != "Semua" and status != status_filter:
                continue

            # Filter tanggal
            if date_filter and date_filter not in tanggal:
                continue

            filtered.append(trx)

        self._populate_table(filtered)
        self.lbl_result_count.setText(f"Menampilkan: {len(filtered)} data")

    def _populate_table(self, data):
        self.tbl.setRowCount(len(data))
        for row, trx in enumerate(data):
            id_, nama, subtotal, pembayaran, status, tanggal, no_invoice = trx
            for col, val in enumerate([
                str(id_), no_invoice, nama, tanggal,
                format_rupiah(subtotal), format_rupiah(pembayaran)
            ]):
                cell = QTableWidgetItem(val)
                cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tbl.setItem(row, col, cell)

            badge = QLabel(status)
            badge.setStyleSheet(BADGE_LUNAS if status == 'LUNAS' else BADGE_BELUM)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tbl.setCellWidget(row, 6, badge)

            action_w = QWidget()
            action_l = QHBoxLayout(action_w)
            action_l.setContentsMargins(4, 2, 4, 2)
            action_l.setSpacing(4)

            # Tombol View dengan warna info
            btn_view = QPushButton("👁")
            btn_view.setFixedWidth(36)
            btn_view.setStyleSheet(TABLE_BTN_VIEW)
            btn_view.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_view.clicked.connect(lambda _, tid=id_: self._view(tid))

            # Tombol Edit dengan warna warning
            btn_edit = QPushButton("✏️")
            btn_edit.setFixedWidth(36)
            btn_edit.setStyleSheet(TABLE_BTN_EDIT)
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit.clicked.connect(lambda _, tid=id_: self._update_bayar(tid))

            # Tombol Print dengan warna success
            btn_print = QPushButton("🖨")
            btn_print.setFixedWidth(36)
            btn_print.setStyleSheet(TABLE_BTN_PRINT)
            btn_print.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_print.clicked.connect(lambda _, tid=id_: self._print(tid))

            # Tombol Hapus dengan warna danger
            btn_hapus = QPushButton("🗑")
            btn_hapus.setFixedWidth(36)
            btn_hapus.setStyleSheet("""
                QPushButton {
                    background-color: #f38ba8;
                    color: #1e1e2e;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 2px;
                }
                QPushButton:hover { background-color: #eb6f92; }
                QPushButton:pressed { background-color: #c94f6d; }
            """)
            btn_hapus.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_hapus.setToolTip("Hapus transaksi (perlu PIN)")
            btn_hapus.clicked.connect(lambda _, tid=id_, inv=no_invoice: self._hapus_transaksi(tid, inv))

            action_l.addWidget(btn_view)
            action_l.addWidget(btn_edit)
            action_l.addWidget(btn_print)
            action_l.addWidget(btn_hapus)
            self.tbl.setCellWidget(row, 7, action_w)

    def _view(self, transaksi_id):
        try:
            detail_data = self.db.get_transaksi_detail(transaksi_id)
            if not detail_data:
                QMessageBox.warning(self, "Warning", "Data tidak ditemukan!")
                return
            dialog = QDialog(self)
            dialog.setWindowTitle("Detail Transaksi")
            dialog.resize(640, 420)
            layout = QVBoxLayout(dialog)
            trx = detail_data[0]
            no_invoice = trx['no_invoice']
            nama_pembeli = trx['nama_pembeli']
            tanggal = trx['tanggal']
            subtotal = trx['subtotal']
            pembayaran = trx['pembayaran']
            status = trx['status']
            info = QLabel(
                f"Invoice: {no_invoice}  |  Pembeli: {nama_pembeli}  |  Tanggal: {tanggal}\n"
                f"Subtotal: {format_rupiah(subtotal)}  |  Pembayaran: {format_rupiah(pembayaran)}  |  Status: {status}")
            info.setStyleSheet(
                "background-color: #24273a; padding: 10px; border-radius: 6px; font-size: 11px; font-weight: bold;")
            layout.addWidget(info)
            tbl = QTableWidget(len(detail_data), 6)
            tbl.setHorizontalHeaderLabels(["Warna", "Kategori", "Ukuran", "Qty", "Harga", "Total"])
            tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            for i, item in enumerate(detail_data):
                qty = item['qty']
                harga = item['harga']
                warna = item['warna']
                kategori = item['kategori']
                ukuran = item['ukuran']
                for j, v in enumerate([warna, kategori, ukuran, str(qty), format_rupiah(harga), format_rupiah(qty * harga)]):
                    c = QTableWidgetItem(v)
                    c.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    tbl.setItem(i, j, c)
            layout.addWidget(tbl)
            btn_close = QPushButton("Tutup")
            btn_close.clicked.connect(dialog.accept)
            layout.addWidget(btn_close)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _update_bayar(self, transaksi_id):
        try:
            all_trx = self.db.get_all_transaksi()
            trx = next((t for t in all_trx if t[0] == transaksi_id), None)
            if not trx:
                return
            dialog = QDialog(self)
            dialog.setWindowTitle("Update Pembayaran")
            dialog.resize(360, 180)
            layout = QFormLayout(dialog)
            layout.setContentsMargins(20, 16, 20, 16)
            info = QLabel(f"Invoice: {trx['no_invoice']}\nSubtotal: {format_rupiah(trx['subtotal'])}\n"
                          f"Pembayaran Saat Ini: {format_rupiah(trx['pembayaran'])}")
            layout.addRow(info)
            edit = QLineEdit(str(trx['pembayaran']))
            layout.addRow("Pembayaran Baru:", edit)
            buttons = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addRow(buttons)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                val = parse_currency(edit.text())
                if val < 0:
                    QMessageBox.warning(self, "Warning", "Pembayaran tidak boleh negatif!")
                    return
                status_baru = self.db.update_pembayaran_transaksi(transaksi_id, val)
                if status_baru == 'LUNAS' and trx['status'] != 'LUNAS':
                    self.invoice_gen.print_invoice(transaksi_id)
                QMessageBox.information(self, "Sukses", f"Pembayaran diupdate.\nStatus: {status_baru}")
                self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _print(self, transaksi_id):
        try:
            filepath = self.invoice_gen.print_invoice(transaksi_id)
            if filepath:
                reply = QMessageBox.question(
                    self, "Invoice",
                    "Invoice berhasil dibuat.\nBuka file PDF sekarang?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    if not open_pdf(filepath):
                        QMessageBox.warning(self, "Gagal", f"Tidak dapat membuka PDF.\nFile tersimpan di:\n{filepath}")
            else:
                QMessageBox.warning(self, "Gagal", "Gagal membuat invoice!")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _hapus_transaksi(self, transaksi_id, no_invoice):
        """Hapus transaksi setelah verifikasi PIN."""
        from ui.settings_ui import PinDialog

        # Step 1: Verifikasi PIN
        pin_dialog = PinDialog(self.db, self)
        pin_dialog.setWindowTitle("🔐  Verifikasi PIN — Hapus Transaksi")
        if pin_dialog.exec() != QDialog.DialogCode.Accepted:
            return

        # Step 2: Konfirmasi hapus
        reply = QMessageBox.warning(
            self, "⚠️  Konfirmasi Hapus",
            f"Anda akan menghapus transaksi:\n\n"
            f"Invoice: {no_invoice}\n\n"
            f"Data yang dihapus tidak dapat dikembalikan!\n"
            f"Lanjutkan?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Step 3: Hapus dari database
        try:
            self.db.delete_transaksi(transaksi_id)
            QMessageBox.information(self, "Sukses", f"Transaksi {no_invoice} berhasil dihapus.")
            self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal menghapus transaksi: {e}")

    def _export(self):
        try:
            success, message = self.excel_export.export_transaksi()
            if success:
                QMessageBox.information(self, "Sukses", message)
            else:
                QMessageBox.warning(self, "Gagal", message)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))