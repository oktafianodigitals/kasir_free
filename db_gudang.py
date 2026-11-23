"""
db_gudang.py - Modul Database Gudang (Warehouse)
Menangani: stok barang, log stok, restock, backup stok
Menggunakan database.db yang sama dengan database utama
"""

import sqlite3
import os
import logging
from datetime import datetime
from contextlib import contextmanager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('db_gudang')

DB_PATH = 'database/database.db'
STOK_MINIMUM_DEFAULT = 10


class DatabaseGudang:
    """
    Modul database khusus untuk manajemen gudang.
    Berbagi file database.db yang sama dengan database utama,
    namun menangani tabel dan logika gudang secara terpisah.
    """

    def __init__(self):
        if not os.path.exists('database'):
            os.makedirs('database')
        self.db_path = DB_PATH
        self.init_gudang_tables()
        logger.info("DatabaseGudang diinisialisasi.")

    @contextmanager
    def get_connection(self):
        """Context manager untuk koneksi database yang aman."""
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

    def init_gudang_tables(self):
        """Inisialisasi tabel-tabel gudang."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Tabel stok barang
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stok_barang (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    warna_id INTEGER NOT NULL,
                    kategori_id INTEGER NOT NULL,
                    ukuran_id INTEGER NOT NULL,
                    jumlah INTEGER NOT NULL DEFAULT 0,
                    stok_minimum INTEGER NOT NULL DEFAULT 10,
                    tanggal_update TEXT NOT NULL,
                    FOREIGN KEY (warna_id) REFERENCES warna(id),
                    FOREIGN KEY (kategori_id) REFERENCES kategori(id),
                    FOREIGN KEY (ukuran_id) REFERENCES ukuran(id),
                    UNIQUE(warna_id, kategori_id, ukuran_id)
                )
            ''')

            # Tabel log stok
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS log_stok (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stok_id INTEGER,
                    warna_id INTEGER NOT NULL,
                    kategori_id INTEGER NOT NULL,
                    ukuran_id INTEGER NOT NULL,
                    stok_lama INTEGER NOT NULL,
                    stok_baru INTEGER NOT NULL,
                    perubahan INTEGER NOT NULL,
                    aksi TEXT NOT NULL,
                    keterangan TEXT,
                    tanggal TEXT NOT NULL
                )
            ''')

            # Tabel backup stok
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stock_backup (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stok_id INTEGER NOT NULL,
                    warna_id INTEGER NOT NULL,
                    kategori_id INTEGER NOT NULL,
                    ukuran_id INTEGER NOT NULL,
                    jumlah INTEGER NOT NULL,
                    tanggal_backup TEXT NOT NULL,
                    keterangan TEXT
                )
            ''')

            # Index untuk performa
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_stok_barang_combo
                ON stok_barang(warna_id, kategori_id, ukuran_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_log_stok_tanggal
                ON log_stok(tanggal)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_backup_tanggal
                ON stock_backup(tanggal_backup)
            ''')

        logger.info("Tabel gudang berhasil diinisialisasi.")

    # ─────────────────────────────────────────────
    # STOK BARANG
    # ─────────────────────────────────────────────

    def get_all_stok(self):
        """Ambil semua stok barang beserta nama warna/kategori/ukuran."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT
                    s.id,
                    w.nama AS warna,
                    k.nama AS kategori,
                    u.nama AS ukuran,
                    s.jumlah,
                    s.stok_minimum,
                    s.tanggal_update,
                    s.warna_id,
                    s.kategori_id,
                    s.ukuran_id
                FROM stok_barang s
                JOIN warna w ON s.warna_id = w.id
                JOIN kategori k ON s.kategori_id = k.id
                JOIN ukuran u ON s.ukuran_id = u.id
                ORDER BY k.nama, w.nama, u.nama
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def get_stok_by_id(self, stok_id):
        """Ambil satu record stok berdasarkan ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.*, w.nama AS warna, k.nama AS kategori, u.nama AS ukuran
                FROM stok_barang s
                JOIN warna w ON s.warna_id = w.id
                JOIN kategori k ON s.kategori_id = k.id
                JOIN ukuran u ON s.ukuran_id = u.id
                WHERE s.id = ?
            ''', (stok_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_stok_by_combo(self, warna_id, kategori_id, ukuran_id):
        """Ambil stok berdasarkan kombinasi warna-kategori-ukuran."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM stok_barang
                WHERE warna_id = ? AND kategori_id = ? AND ukuran_id = ?
            ''', (warna_id, kategori_id, ukuran_id))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_or_update_stok(self, warna_id, kategori_id, ukuran_id,
                           jumlah, stok_minimum=STOK_MINIMUM_DEFAULT, keterangan="Stok awal"):
        """Tambah atau update stok barang, catat log dan backup."""
        tanggal = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        existing = self.get_stok_by_combo(warna_id, kategori_id, ukuran_id)

        with self.get_connection() as conn:
            cursor = conn.cursor()

            if existing:
                stok_lama = existing['jumlah']
                cursor.execute('''
                    UPDATE stok_barang
                    SET jumlah = ?, stok_minimum = ?, tanggal_update = ?
                    WHERE id = ?
                ''', (jumlah, stok_minimum, tanggal, existing['id']))
                stok_id = existing['id']
                aksi = "UPDATE"
            else:
                cursor.execute('''
                    INSERT INTO stok_barang
                    (warna_id, kategori_id, ukuran_id, jumlah, stok_minimum, tanggal_update)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (warna_id, kategori_id, ukuran_id, jumlah, stok_minimum, tanggal))
                stok_id = cursor.lastrowid
                stok_lama = 0
                aksi = "INSERT"

            perubahan = jumlah - stok_lama

            # Log stok
            cursor.execute('''
                INSERT INTO log_stok
                (stok_id, warna_id, kategori_id, ukuran_id,
                 stok_lama, stok_baru, perubahan, aksi, keterangan, tanggal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (stok_id, warna_id, kategori_id, ukuran_id,
                  stok_lama, jumlah, perubahan, aksi, keterangan, tanggal))

            # Backup stok
            cursor.execute('''
                INSERT INTO stock_backup
                (stok_id, warna_id, kategori_id, ukuran_id, jumlah, tanggal_backup, keterangan)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (stok_id, warna_id, kategori_id, ukuran_id, jumlah, tanggal, keterangan))

        logger.info(f"Stok {aksi}: id={stok_id}, jumlah={jumlah}")
        return stok_id

    def restock(self, stok_id, tambah_qty, keterangan="Restock"):
        """Tambah jumlah stok (restock)."""
        stok = self.get_stok_by_id(stok_id)
        if not stok:
            raise ValueError(f"Stok ID {stok_id} tidak ditemukan.")

        jumlah_baru = stok['jumlah'] + tambah_qty
        return self.add_or_update_stok(
            stok['warna_id'], stok['kategori_id'], stok['ukuran_id'],
            jumlah_baru, stok['stok_minimum'], keterangan
        )

    def kurangi_stok(self, warna_id, kategori_id, ukuran_id, qty, keterangan="Penjualan"):
        """
        Kurangi stok setelah transaksi penjualan.
        Dipanggil oleh database.py setelah transaksi berhasil.
        """
        stok = self.get_stok_by_combo(warna_id, kategori_id, ukuran_id)
        if not stok:
            logger.warning(f"Stok tidak ditemukan untuk warna={warna_id}, "
                           f"kategori={kategori_id}, ukuran={ukuran_id}. "
                           f"Membuat record stok baru dengan qty 0.")
            stok_id = self.add_or_update_stok(
                warna_id, kategori_id, ukuran_id, 0,
                keterangan="Auto-create saat penjualan"
            )
            stok = self.get_stok_by_id(stok_id)

        jumlah_baru = max(0, stok['jumlah'] - qty)
        self.add_or_update_stok(
            stok['warna_id'], stok['kategori_id'], stok['ukuran_id'],
            jumlah_baru, stok['stok_minimum'], keterangan
        )
        logger.info(f"Stok dikurangi: {stok['jumlah']} → {jumlah_baru} (qty={qty})")
        return jumlah_baru

    def update_stok_minimum(self, stok_id, stok_minimum):
        """Update nilai stok minimum alert."""
        tanggal = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE stok_barang SET stok_minimum = ?, tanggal_update = ?
                WHERE id = ?
            ''', (stok_minimum, tanggal, stok_id))
        logger.info(f"Stok minimum diupdate: id={stok_id}, minimum={stok_minimum}")

    def delete_stok(self, stok_id):
        """Hapus record stok (log tetap tersimpan)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM stok_barang WHERE id = ?', (stok_id,))
        logger.info(f"Stok dihapus: id={stok_id}")

    # ─────────────────────────────────────────────
    # STOK ALERT
    # ─────────────────────────────────────────────

    def get_stok_menipis(self):
        """Ambil stok yang jumlahnya > 0 tapi <= stok_minimum (tidak termasuk habis)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT
                    s.id, w.nama AS warna, k.nama AS kategori,
                    u.nama AS ukuran, s.jumlah, s.stok_minimum
                FROM stok_barang s
                JOIN warna w ON s.warna_id = w.id
                JOIN kategori k ON s.kategori_id = k.id
                JOIN ukuran u ON s.ukuran_id = u.id
                WHERE s.jumlah > 0 AND s.jumlah <= s.stok_minimum
                ORDER BY s.jumlah ASC
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def get_stok_habis(self):
        """Ambil stok yang jumlahnya = 0."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.id, w.nama AS warna, k.nama AS kategori, u.nama AS ukuran
                FROM stok_barang s
                JOIN warna w ON s.warna_id = w.id
                JOIN kategori k ON s.kategori_id = k.id
                JOIN ukuran u ON s.ukuran_id = u.id
                WHERE s.jumlah = 0
            ''')
            return [dict(row) for row in cursor.fetchall()]

    # ─────────────────────────────────────────────
    # LOG STOK
    # ─────────────────────────────────────────────

    def get_log_stok(self, limit=100):
        """Ambil log perubahan stok terbaru."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT
                    l.id, w.nama AS warna, k.nama AS kategori,
                    u.nama AS ukuran, l.stok_lama, l.stok_baru,
                    l.perubahan, l.aksi, l.keterangan, l.tanggal
                FROM log_stok l
                JOIN warna w ON l.warna_id = w.id
                JOIN kategori k ON l.kategori_id = k.id
                JOIN ukuran u ON l.ukuran_id = u.id
                ORDER BY l.tanggal DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # ─────────────────────────────────────────────
    # BACKUP STOK
    # ─────────────────────────────────────────────

    def get_backup_stok(self, limit=100):
        """Ambil riwayat backup stok."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT
                    b.id, w.nama AS warna, k.nama AS kategori,
                    u.nama AS ukuran, b.jumlah, b.tanggal_backup, b.keterangan
                FROM stock_backup b
                JOIN warna w ON b.warna_id = w.id
                JOIN kategori k ON b.kategori_id = k.id
                JOIN ukuran u ON b.ukuran_id = u.id
                ORDER BY b.tanggal_backup DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # ─────────────────────────────────────────────
    # STATISTIK GUDANG
    # ─────────────────────────────────────────────

    def get_statistik_gudang(self):
        """Ambil statistik ringkas gudang."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM stok_barang')
            total_item = cursor.fetchone()[0]

            cursor.execute('SELECT SUM(jumlah) FROM stok_barang')
            total_stok = cursor.fetchone()[0] or 0

            cursor.execute('SELECT COUNT(*) FROM stok_barang WHERE jumlah = 0')
            stok_habis = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM stok_barang WHERE jumlah <= stok_minimum AND jumlah > 0')
            stok_menipis = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM log_stok')
            total_log = cursor.fetchone()[0]

        return {
            'total_item': total_item,
            'total_stok': total_stok,
            'stok_habis': stok_habis,
            'stok_menipis': stok_menipis,
            'total_log': total_log,
        }
