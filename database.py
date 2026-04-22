"""
database.py - Modul Database Utama
Menangani: transaksi, produk (warna/kategori/ukuran), pelanggan, laporan, pengaturan
Kompatibel penuh dengan invoice.py dan export.py (excel.py)
"""

import sqlite3
import os
import logging
from datetime import datetime
from contextlib import contextmanager

logger = logging.getLogger('database')

DB_PATH = 'database/database.db'


class Database:
    """
    Database utama sistem kasir.
    Menangani transaksi, produk, dan integrasi dengan invoice & export.
    """

    def __init__(self):
        if not os.path.exists('database'):
            os.makedirs('database')
        self.db_path = DB_PATH
        self.init_database()
        logger.info("Database utama diinisialisasi.")

    @contextmanager
    def _get_conn(self):
        """Context manager koneksi aman dengan WAL mode."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def get_connection(self):
        """Mengembalikan raw connection untuk kompatibilitas dengan invoice.py & export.py."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def init_database(self):
        """Inisialisasi semua tabel database."""
        with self._get_conn() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS warna (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nama TEXT NOT NULL UNIQUE
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS kategori (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nama TEXT NOT NULL UNIQUE
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ukuran (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nama TEXT NOT NULL UNIQUE
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transaksi (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nama_pembeli TEXT NOT NULL,
                    subtotal INTEGER NOT NULL,
                    pembayaran INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    tanggal TEXT NOT NULL,
                    no_invoice TEXT NOT NULL UNIQUE
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS detail_transaksi (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaksi_id INTEGER NOT NULL,
                    warna_id INTEGER NOT NULL,
                    kategori_id INTEGER NOT NULL,
                    ukuran_id INTEGER NOT NULL,
                    qty INTEGER NOT NULL,
                    harga INTEGER NOT NULL,
                    FOREIGN KEY (transaksi_id) REFERENCES transaksi(id),
                    FOREIGN KEY (warna_id) REFERENCES warna(id),
                    FOREIGN KEY (kategori_id) REFERENCES kategori(id),
                    FOREIGN KEY (ukuran_id) REFERENCES ukuran(id)
                )
            ''')

            # Tabel pengaturan toko
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pengaturan (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nama_toko TEXT NOT NULL DEFAULT 'SABLON KAOS MANADO',
                    alamat_toko TEXT NOT NULL DEFAULT 'Jln. Karombasan selatan 1, Rt 07 Rw 05',
                    pin_akses TEXT NOT NULL DEFAULT '123456'
                )
            ''')

            # Index untuk performa query transaksi
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_transaksi_tanggal
                ON transaksi(tanggal)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_detail_transaksi_id
                ON detail_transaksi(transaksi_id)
            ''')

        self._insert_default_data()
        self._insert_default_pengaturan()

    def _insert_default_data(self):
        """Insert data default warna, kategori, ukuran."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM warna')
            warna_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM kategori')
            kategori_count = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM ukuran')
            ukuran_count = cursor.fetchone()[0]
            if warna_count == 0:
                for nama in ['Putih', 'Hitam', 'Merah', 'Biru', 'Hijau', 'Kuning']:
                    cursor.execute('INSERT INTO warna (nama) VALUES (?)', (nama,))
            if kategori_count == 0:
                for nama in ['Kaos Polos', 'Kaos Sablon', 'Polo Shirt', 'Hoodie', 'Jaket']:
                    cursor.execute('INSERT INTO kategori (nama) VALUES (?)', (nama,))
            if ukuran_count == 0:
                for nama in ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL']:
                    cursor.execute('INSERT INTO ukuran (nama) VALUES (?)', (nama,))

    def _insert_default_pengaturan(self):
        """Insert data pengaturan default jika belum ada."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM pengaturan')
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.execute('''INSERT INTO pengaturan (nama_toko, alamat_toko, pin_akses)
                    VALUES ('SABLON KAOS MANADO', 'Jln. Karombasan selatan 1, Rt 07 Rw 05', '123456')''')
                logger.info("Data pengaturan default diinsert.")

    # ─────────────────────────────────────────────
    # PENGATURAN
    # ─────────────────────────────────────────────

    def get_pengaturan(self):
        """Ambil data pengaturan toko."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM pengaturan WHERE id = 1')
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_pengaturan(self, nama_toko=None, alamat_toko=None, pin_akses=None):
        """Update data pengaturan toko."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            current = self.get_pengaturan()
            if not current:
                return False
            nama_toko = nama_toko if nama_toko is not None else current['nama_toko']
            alamat_toko = alamat_toko if alamat_toko is not None else current['alamat_toko']
            pin_akses = pin_akses if pin_akses is not None else current['pin_akses']
            cursor.execute('''UPDATE pengaturan SET nama_toko = ?, alamat_toko = ?, pin_akses = ?
                WHERE id = 1''', (nama_toko, alamat_toko, pin_akses))
            logger.info("Pengaturan toko diupdate.")
            return True

    def verifikasi_pin(self, pin):
        """Verifikasi PIN akses."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT pin_akses FROM pengaturan WHERE id = 1')
            row = cursor.fetchone()
            if row and row[0] == pin:
                return True
            return False

    # ─────────────────────────────────────────────
    # WARNA CRUD
    # ─────────────────────────────────────────────

    def get_all_warna(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, nama FROM warna ORDER BY nama')
            return cursor.fetchall()

    def add_warna(self, nama):
        try:
            with self._get_conn() as conn:
                conn.cursor().execute('INSERT INTO warna (nama) VALUES (?)', (nama,))
            return True
        except sqlite3.IntegrityError:
            return False

    def update_warna(self, id, nama):
        try:
            with self._get_conn() as conn:
                conn.cursor().execute('UPDATE warna SET nama = ? WHERE id = ?', (nama, id))
            return True
        except sqlite3.IntegrityError:
            return False

    def delete_warna(self, id):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM detail_transaksi WHERE warna_id = ?', (id,))
            if cursor.fetchone()[0] > 0:
                raise ValueError("Warna tidak dapat dihapus karena masih digunakan dalam transaksi.")
            cursor.execute('SELECT COUNT(*) FROM stok_barang WHERE warna_id = ?', (id,))
            if cursor.fetchone()[0] > 0:
                raise ValueError("Warna tidak dapat dihapus karena masih digunakan dalam data stok gudang.")
            cursor.execute('DELETE FROM warna WHERE id = ?', (id,))

    # ─────────────────────────────────────────────
    # KATEGORI CRUD
    # ─────────────────────────────────────────────

    def get_all_kategori(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, nama FROM kategori ORDER BY nama')
            return cursor.fetchall()

    def add_kategori(self, nama):
        try:
            with self._get_conn() as conn:
                conn.cursor().execute('INSERT INTO kategori (nama) VALUES (?)', (nama,))
            return True
        except sqlite3.IntegrityError:
            return False

    def update_kategori(self, id, nama):
        try:
            with self._get_conn() as conn:
                conn.cursor().execute('UPDATE kategori SET nama = ? WHERE id = ?', (nama, id))
            return True
        except sqlite3.IntegrityError:
            return False

    def delete_kategori(self, id):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM detail_transaksi WHERE kategori_id = ?', (id,))
            if cursor.fetchone()[0] > 0:
                raise ValueError("Kategori tidak dapat dihapus karena masih digunakan dalam transaksi.")
            cursor.execute('SELECT COUNT(*) FROM stok_barang WHERE kategori_id = ?', (id,))
            if cursor.fetchone()[0] > 0:
                raise ValueError("Kategori tidak dapat dihapus karena masih digunakan dalam data stok gudang.")
            cursor.execute('DELETE FROM kategori WHERE id = ?', (id,))

    # ─────────────────────────────────────────────
    # UKURAN CRUD
    # ─────────────────────────────────────────────

    def get_all_ukuran(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, nama FROM ukuran ORDER BY nama')
            return cursor.fetchall()

    def add_ukuran(self, nama):
        try:
            with self._get_conn() as conn:
                conn.cursor().execute('INSERT INTO ukuran (nama) VALUES (?)', (nama,))
            return True
        except sqlite3.IntegrityError:
            return False

    def update_ukuran(self, id, nama):
        try:
            with self._get_conn() as conn:
                conn.cursor().execute('UPDATE ukuran SET nama = ? WHERE id = ?', (nama, id))
            return True
        except sqlite3.IntegrityError:
            return False

    def delete_ukuran(self, id):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM detail_transaksi WHERE ukuran_id = ?', (id,))
            if cursor.fetchone()[0] > 0:
                raise ValueError("Ukuran tidak dapat dihapus karena masih digunakan dalam transaksi.")
            cursor.execute('SELECT COUNT(*) FROM stok_barang WHERE ukuran_id = ?', (id,))
            if cursor.fetchone()[0] > 0:
                raise ValueError("Ukuran tidak dapat dihapus karena masih digunakan dalam data stok gudang.")
            cursor.execute('DELETE FROM ukuran WHERE id = ?', (id,))

    # ─────────────────────────────────────────────
    # TRANSAKSI
    # ─────────────────────────────────────────────

    def generate_invoice_number(self):
        """Generate nomor invoice otomatis: INV-YYYYMMDD-XXX."""
        today = datetime.now().strftime('%Y%m%d')
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT no_invoice FROM transaksi WHERE no_invoice LIKE ? ORDER BY no_invoice DESC LIMIT 1", (f'INV-{today}-%',))
            row = cursor.fetchone()
            if row:
                try:
                    last_seq = int(row[0].split('-')[-1])
                except (ValueError, IndexError):
                    last_seq = 0
            else:
                last_seq = 0
        return f'INV-{today}-{last_seq + 1:03d}'

    def add_transaksi(self, nama_pembeli, subtotal, pembayaran, detail_items):
        """Tambah transaksi baru beserta detail."""
        self._validasi_stok(detail_items)
        no_invoice = self.generate_invoice_number()
        status = 'LUNAS' if pembayaran >= subtotal else 'BELUM LUNAS'
        tanggal = datetime.now().strftime('%Y-%m-%d')
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO transaksi (nama_pembeli, subtotal, pembayaran, status, tanggal, no_invoice)
                VALUES (?, ?, ?, ?, ?, ?)''', (nama_pembeli, subtotal, pembayaran, status, tanggal, no_invoice))
            transaksi_id = cursor.lastrowid
            for item in detail_items:
                cursor.execute('''INSERT INTO detail_transaksi
                    (transaksi_id, warna_id, kategori_id, ukuran_id, qty, harga)
                    VALUES (?, ?, ?, ?, ?, ?)''', (transaksi_id, item['warna_id'], item['kategori_id'], item['ukuran_id'], item['qty'], item['harga']))
        self._update_stok_setelah_transaksi(detail_items, no_invoice)
        logger.info(f"Transaksi baru: {no_invoice}, total={subtotal}, status={status}")
        return {'transaksi_id': transaksi_id, 'no_invoice': no_invoice, 'status': status, 'tanggal': tanggal}
        
    def _validasi_stok(self, detail_items):
        """Validasi ketersediaan stok untuk semua item."""
        try:
            from db_gudang import DatabaseGudang
            db_gudang = DatabaseGudang()
        except Exception:
            return
        errors = []
        for item in detail_items:
            stok = db_gudang.get_stok_by_combo(item['warna_id'], item['kategori_id'], item['ukuran_id'])
            stok_tersedia = stok['jumlah'] if stok else 0
            with self._get_conn() as conn:
                cursor = conn.cursor()
                
                # Simpan hasil fetchone() ke variabel terlebih dahulu
                cursor.execute('SELECT nama FROM warna WHERE id = ?', (item['warna_id'],))
                row = cursor.fetchone()
                warna = row[0] if row else f"ID={item['warna_id']}"
                
                cursor.execute('SELECT nama FROM kategori WHERE id = ?', (item['kategori_id'],))
                row = cursor.fetchone()
                kategori = row[0] if row else f"ID={item['kategori_id']}"
                
                cursor.execute('SELECT nama FROM ukuran WHERE id = ?', (item['ukuran_id'],))
                row = cursor.fetchone()
                ukuran = row[0] if row else f"ID={item['ukuran_id']}"
                
            if stok_tersedia == 0:
                errors.append(f"• {kategori} / {warna} / {ukuran}: STOK HABIS")
            elif stok_tersedia < item['qty']:
                errors.append(f"• {kategori} / {warna} / {ukuran}: stok hanya {stok_tersedia}, dibutuhkan {item['qty']}")
        if errors:
            raise ValueError("Transaksi gagal, stok tidak mencukupi:\n" + "\n".join(errors))

    # def _validasi_stok(self, detail_items):
    #     """Validasi ketersediaan stok untuk semua item."""
    #     try:
    #         from db_gudang import DatabaseGudang
    #         db_gudang = DatabaseGudang()
    #     except Exception:
    #         return
    #     errors = []
    #     for item in detail_items:
    #         stok = db_gudang.get_stok_by_combo(item['warna_id'], item['kategori_id'], item['ukuran_id'])
    #         stok_tersedia = stok['jumlah'] if stok else 0
    #         with self._get_conn() as conn:
    #             cursor = conn.cursor()
    #             cursor.execute('SELECT nama FROM warna WHERE id = ?', (item['warna_id'],))
    #             warna = cursor.fetchone()[0] if cursor.fetchone() else f"ID={item['warna_id']}"
    #             cursor.execute('SELECT nama FROM kategori WHERE id = ?', (item['kategori_id'],))
    #             kategori = cursor.fetchone()[0] if cursor.fetchone() else f"ID={item['kategori_id']}"
    #             cursor.execute('SELECT nama FROM ukuran WHERE id = ?', (item['ukuran_id'],))
    #             ukuran = cursor.fetchone()[0] if cursor.fetchone() else f"ID={item['ukuran_id']}"
    #         if stok_tersedia == 0:
    #             errors.append(f"• {kategori} / {warna} / {ukuran}: STOK HABIS")
    #         elif stok_tersedia < item['qty']:
    #             errors.append(f"• {kategori} / {warna} / {ukuran}: stok hanya {stok_tersedia}, dibutuhkan {item['qty']}")
    #     if errors:
    #         raise ValueError("Transaksi gagal, stok tidak mencukupi:\n" + "\n".join(errors))

    def _update_stok_setelah_transaksi(self, detail_items, no_invoice):
        """Kurangi stok gudang untuk setiap item yang terjual."""
        try:
            from db_gudang import DatabaseGudang
            db_gudang = DatabaseGudang()
            for item in detail_items:
                db_gudang.kurangi_stok(warna_id=item['warna_id'], kategori_id=item['kategori_id'], ukuran_id=item['ukuran_id'], qty=item['qty'], keterangan=f"Penjualan {no_invoice}")
        except Exception as e:
            logger.warning(f"Gagal update stok gudang: {e}")

    def get_all_transaksi(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, nama_pembeli, subtotal, pembayaran, status, tanggal, no_invoice FROM transaksi ORDER BY id DESC')
            return cursor.fetchall()

    def get_transaksi_detail(self, transaksi_id):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''SELECT t.*, dt.qty, dt.harga, w.nama AS warna, k.nama AS kategori, u.nama AS ukuran
                FROM transaksi t JOIN detail_transaksi dt ON t.id = dt.transaksi_id
                JOIN warna w ON dt.warna_id = w.id JOIN kategori k ON dt.kategori_id = k.id
                JOIN ukuran u ON dt.ukuran_id = u.id WHERE t.id = ?''', (transaksi_id,))
            return cursor.fetchall()

    def update_pembayaran_transaksi(self, transaksi_id, pembayaran_baru):
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT subtotal FROM transaksi WHERE id = ?', (transaksi_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Transaksi ID {transaksi_id} tidak ditemukan.")
            subtotal = row[0]
            status_baru = 'LUNAS' if pembayaran_baru >= subtotal else 'BELUM LUNAS'
            cursor.execute('UPDATE transaksi SET pembayaran = ?, status = ? WHERE id = ?', (pembayaran_baru, status_baru, transaksi_id))
        return status_baru

    def delete_transaksi(self, transaksi_id):
        """Hapus transaksi beserta detailnya dari database."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM transaksi WHERE id = ?', (transaksi_id,))
            if not cursor.fetchone():
                raise ValueError(f"Transaksi ID {transaksi_id} tidak ditemukan.")
            cursor.execute('DELETE FROM detail_transaksi WHERE transaksi_id = ?', (transaksi_id,))
            cursor.execute('DELETE FROM transaksi WHERE id = ?', (transaksi_id,))

    # ─────────────────────────────────────────────
    # LAPORAN / STATISTIK
    # ─────────────────────────────────────────────

    def get_statistik_dashboard(self):
        """Statistik ringkas untuk dashboard utama."""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM transaksi')
            total_transaksi = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM transaksi WHERE status = 'LUNAS'")
            transaksi_lunas = cursor.fetchone()[0]
            cursor.execute("SELECT SUM(subtotal) FROM transaksi WHERE status = 'LUNAS'")
            total_pendapatan = cursor.fetchone()[0] or 0
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('SELECT COUNT(*) FROM transaksi WHERE tanggal = ?', (today,))
            transaksi_hari_ini = cursor.fetchone()[0]
            cursor.execute("SELECT SUM(subtotal) FROM transaksi WHERE tanggal = ? AND status = 'LUNAS'", (today,))
            pendapatan_hari_ini = cursor.fetchone()[0] or 0
        return {'total_transaksi': total_transaksi, 'transaksi_lunas': transaksi_lunas, 'total_pendapatan': total_pendapatan, 'transaksi_hari_ini': transaksi_hari_ini, 'pendapatan_hari_ini': pendapatan_hari_ini}

    # ─────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────

    @staticmethod
    def format_rupiah(amount):
        """Format angka ke format Rupiah."""
        return f"Rp {amount:,}".replace(',', '.')