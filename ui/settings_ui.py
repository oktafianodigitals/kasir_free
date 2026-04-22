"""
ui/settings_ui.py - UI Pengaturan (PIN, Nama Toko, Alamat)
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFormLayout, QGroupBox, QMessageBox, QDialog,
    QDialogButtonBox, QFrame
)
from PyQt6.QtCore import Qt

logger = logging.getLogger('settings_ui')


class PinDialog(QDialog):
    """Dialog untuk memverifikasi PIN sebelum mengakses pengaturan."""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Verifikasi PIN")
        self.setFixedSize(320, 180)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Icon dan judul
        title = QLabel("🔐  Masukkan PIN Akses")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #cba6f7;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # PIN input
        self.pin_input = QLineEdit()
        self.pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_input.setPlaceholderText("Masukkan 6 digit PIN")
        self.pin_input.setMaxLength(6)
        self.pin_input.setStyleSheet("""
            QLineEdit {
                background-color: #313244;
                color: #cdd6f4;
                border: 2px solid #45475a;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
                letter-spacing: 4px;
            }
            QLineEdit:focus {
                border: 2px solid #cba6f7;
            }
        """)
        layout.addWidget(self.pin_input)

        # Info label
        info = QLabel("PIN default: 123456")
        info.setStyleSheet("color: #6c7086; font-size: 10px;")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("Masuk")
        btn_ok.setProperty("class", "success")
        btn_ok.clicked.connect(self._verify_pin)
        btn_cancel = QPushButton("Batal")
        btn_cancel.setProperty("class", "secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

        self.pin_input.returnPressed.connect(self._verify_pin)
        self.pin_input.setFocus()

    def _verify_pin(self):
        pin = self.pin_input.text().strip()
        if not pin:
            QMessageBox.warning(self, "Warning", "PIN tidak boleh kosong!")
            return
        if self.db.verifikasi_pin(pin):
            self.accept()
        else:
            QMessageBox.warning(self, "PIN Salah", "PIN yang Anda masukkan tidak benar.")
            self.pin_input.clear()
            self.pin_input.setFocus()


class SettingsTab(QWidget):
    """Tab Pengaturan - mengelola nama toko, alamat, dan PIN."""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._is_unlocked = False
        self._init_ui()
        self._load_settings()
        self._lock_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # Header
        header = QHBoxLayout()
        title = QLabel("⚙️  Pengaturan")
        title.setObjectName("section_title")
        header.addWidget(title)
        
        self.lock_status = QLabel("🔒 Terkunci")
        self.lock_status.setStyleSheet("color: #f38ba8; font-weight: bold; font-size: 12px;")
        header.addWidget(self.lock_status)
        header.addStretch()
        
        self.btn_unlock = QPushButton("🔓 Buka Kunci")
        self.btn_unlock.setProperty("class", "success")
        self.btn_unlock.clicked.connect(self._show_pin_dialog)
        header.addWidget(self.btn_unlock)
        
        root.addLayout(header)

        # Content area
        self.content_frame = QFrame()
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setSpacing(16)

        # Group: Informasi Toko
        toko_group = QGroupBox("🏪  Informasi Toko")
        toko_layout = QFormLayout(toko_group)
        toko_layout.setSpacing(12)

        self.nama_toko_input = QLineEdit()
        self.nama_toko_input.setPlaceholderText("Nama toko Anda")
        toko_layout.addRow("Nama Toko:", self.nama_toko_input)

        self.alamat_toko_input = QLineEdit()
        self.alamat_toko_input.setPlaceholderText("Alamat lengkap toko")
        toko_layout.addRow("Alamat Toko:", self.alamat_toko_input)

        content_layout.addWidget(toko_group)

        # Group: Keamanan (PIN)
        pin_group = QGroupBox("🔐  Keamanan - PIN Akses")
        pin_layout = QFormLayout(pin_group)
        pin_layout.setSpacing(12)

        self.pin_lama_input = QLineEdit()
        self.pin_lama_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_lama_input.setPlaceholderText("PIN saat ini")
        self.pin_lama_input.setMaxLength(6)
        pin_layout.addRow("PIN Lama:", self.pin_lama_input)

        self.pin_baru_input = QLineEdit()
        self.pin_baru_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_baru_input.setPlaceholderText("PIN baru (6 digit)")
        self.pin_baru_input.setMaxLength(6)
        pin_layout.addRow("PIN Baru:", self.pin_baru_input)

        self.pin_konfirmasi_input = QLineEdit()
        self.pin_konfirmasi_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_konfirmasi_input.setPlaceholderText("Ulangi PIN baru")
        self.pin_konfirmasi_input.setMaxLength(6)
        pin_layout.addRow("Konfirmasi PIN:", self.pin_konfirmasi_input)

        info_pin = QLabel("ℹ️  PIN harus 6 digit angka. PIN default: 123456")
        info_pin.setStyleSheet("color: #6c7086; font-size: 10px;")
        pin_layout.addRow(info_pin)

        content_layout.addWidget(pin_group)

        # Tombol Simpan
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_simpan = QPushButton("💾  Simpan Perubahan")
        self.btn_simpan.setProperty("class", "success")
        self.btn_simpan.clicked.connect(self._simpan_pengaturan)
        btn_layout.addWidget(self.btn_simpan)
        
        self.btn_reset = QPushButton("🔄  Reset")
        self.btn_reset.setProperty("class", "secondary")
        self.btn_reset.clicked.connect(self._load_settings)
        btn_layout.addWidget(self.btn_reset)
        
        content_layout.addLayout(btn_layout)
        content_layout.addStretch()

        root.addWidget(self.content_frame)

    def _lock_ui(self):
        """Kunci UI pengaturan."""
        self._is_unlocked = False
        self.content_frame.setEnabled(False)
        self.lock_status.setText("🔒 Terkunci")
        self.lock_status.setStyleSheet("color: #f38ba8; font-weight: bold; font-size: 12px;")
        self.btn_unlock.setText("🔓 Buka Kunci")
        self.btn_unlock.setProperty("class", "success")
        self.btn_unlock.style().unpolish(self.btn_unlock)
        self.btn_unlock.style().polish(self.btn_unlock)

    def _unlock_ui(self):
        """Buka kunci UI pengaturan."""
        self._is_unlocked = True
        self.content_frame.setEnabled(True)
        self.lock_status.setText("🔓 Terbuka")
        self.lock_status.setStyleSheet("color: #a6e3a1; font-weight: bold; font-size: 12px;")
        self.btn_unlock.setText("🔒 Kunci")
        self.btn_unlock.setProperty("class", "danger")
        self.btn_unlock.style().unpolish(self.btn_unlock)
        self.btn_unlock.style().polish(self.btn_unlock)

    def _show_pin_dialog(self):
        """Tampilkan dialog PIN untuk verifikasi."""
        if self._is_unlocked:
            # Jika sudah terbuka, kunci kembali
            self._lock_ui()
            return
        
        dialog = PinDialog(self.db, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._unlock_ui()
            QMessageBox.information(self, "Sukses", "Pengaturan berhasil dibuka!")

    def _load_settings(self):
        """Load pengaturan dari database."""
        try:
            pengaturan = self.db.get_pengaturan()
            if pengaturan:
                self.nama_toko_input.setText(pengaturan.get('nama_toko', ''))
                self.alamat_toko_input.setText(pengaturan.get('alamat_toko', ''))
            # Clear PIN fields
            self.pin_lama_input.clear()
            self.pin_baru_input.clear()
            self.pin_konfirmasi_input.clear()
        except Exception as e:
            logger.error(f"Gagal load pengaturan: {e}")
            QMessageBox.critical(self, "Error", f"Gagal memuat pengaturan: {e}")

    def _simpan_pengaturan(self):
        """Simpan pengaturan ke database."""
        try:
            nama_toko = self.nama_toko_input.text().strip()
            alamat_toko = self.alamat_toko_input.text().strip()
            pin_lama = self.pin_lama_input.text().strip()
            pin_baru = self.pin_baru_input.text().strip()
            pin_konfirmasi = self.pin_konfirmasi_input.text().strip()

            # Validasi
            if not nama_toko:
                QMessageBox.warning(self, "Warning", "Nama toko tidak boleh kosong!")
                return
            if not alamat_toko:
                QMessageBox.warning(self, "Warning", "Alamat toko tidak boleh kosong!")
                return

            # Update nama dan alamat toko
            self.db.update_pengaturan(nama_toko=nama_toko, alamat_toko=alamat_toko)

            # Update PIN jika diisi
            if pin_baru or pin_konfirmasi or pin_lama:
                if not pin_lama:
                    QMessageBox.warning(self, "Warning", "Masukkan PIN lama untuk mengubah PIN!")
                    return
                if not self.db.verifikasi_pin(pin_lama):
                    QMessageBox.warning(self, "Warning", "PIN lama tidak benar!")
                    self.pin_lama_input.clear()
                    return
                if len(pin_baru) != 6 or not pin_baru.isdigit():
                    QMessageBox.warning(self, "Warning", "PIN baru harus 6 digit angka!")
                    return
                if pin_baru != pin_konfirmasi:
                    QMessageBox.warning(self, "Warning", "PIN baru dan konfirmasi PIN tidak cocok!")
                    return
                self.db.update_pengaturan(pin_akses=pin_baru)
                self.pin_lama_input.clear()
                self.pin_baru_input.clear()
                self.pin_konfirmasi_input.clear()

            QMessageBox.information(self, "Sukses", "Pengaturan berhasil disimpan!")
            logger.info("Pengaturan berhasil diupdate.")
        except Exception as e:
            logger.error(f"Gagal simpan pengaturan: {e}")
            QMessageBox.critical(self, "Error", f"Gagal menyimpan pengaturan: {e}")

    def refresh(self):
        """Refresh data pengaturan."""
        self._load_settings()