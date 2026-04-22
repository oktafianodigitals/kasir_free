import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.flowables import Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.shapes import Drawing, Line, Rect
from reportlab.graphics import renderPDF
from reportlab.platypus.flowables import Flowable
import qrcode
from io import BytesIO
from PIL import Image as PILImage, ImageDraw, ImageFont
from database import Database

class DecorativeLine(Flowable):
    """Custom flowable untuk garis dekoratif yang konsisten dan presisi"""
    def __init__(self, width=None, style='double'):
        Flowable.__init__(self)
        self.width = width if width else 482
        self.style = style
        self.height = 10 if style == 'double' else 6
    
    def draw(self):
        self.canv.saveState()
        if self.style == 'double':
            self.canv.setStrokeColor(colors.HexColor('#2E5BBA'))
            self.canv.setLineWidth(2.5)
            self.canv.line(0, 7, self.width, 7)
            self.canv.setLineWidth(1.2)
            self.canv.line(0, 3, self.width, 3)
        elif self.style == 'gradient':
            for i in range(10):
                alpha = 0.8 - (i * 0.07)
                self.canv.setStrokeColor(colors.Color(0.18, 0.36, 0.73, alpha=alpha))
                self.canv.setLineWidth(2.0 - (i * 0.1))
                y_pos = 4 - (i * 0.15)
                self.canv.line(0, y_pos, self.width - (i * 12), y_pos)
        else:
            self.canv.setStrokeColor(colors.HexColor('#2E5BBA'))
            self.canv.setLineWidth(2.5)
            self.canv.line(0, 3, self.width, 3)
        self.canv.restoreState()

class CustomDocTemplate(SimpleDocTemplate):
    """Custom document template dengan watermark terintegrasi"""
    def __init__(self, filename, status="", **kwargs):
        SimpleDocTemplate.__init__(self, filename, **kwargs)
        self.status = status
    
    def afterPage(self):
        if self.status in ["LUNAS"]:
            self.draw_watermark()
    
    def draw_watermark(self):
        canvas = self.canv
        canvas.saveState()
        canvas.translate(297.5, 421)
        canvas.rotate(45)
        if self.status == "LUNAS":
            canvas.setFont("Helvetica-Bold", 65)
            canvas.setFillColor(colors.Color(0, 0.7, 0, alpha=0.12))
            canvas.drawCentredString(0, 0, "LUNAS")
        else:
            canvas.setFont("Helvetica-Bold", 48)
            canvas.setFillColor(colors.Color(0.8, 0, 0, alpha=0.12))
            canvas.drawCentredString(0, 0, "BELUM LUNAS")
        canvas.restoreState()

class InvoiceGenerator:
    def __init__(self):
        self.db = Database()
        os.makedirs('invoice/lunas', exist_ok=True)
        os.makedirs('invoice/belum_lunas', exist_ok=True)
        
        # Ambil identitas toko dari database
        pengaturan = self.db.get_pengaturan()
        if pengaturan:
            self.nama_toko = pengaturan.get('nama_toko')
            self.alamat_toko = pengaturan.get('alamat_toko')
        else:
            self.nama_toko = "PINGKAN STORE"
            self.alamat_toko = "Jln. Karombasan selatan 1, Rt 07 Rw 05"
        
        self.page_width = 595.276
        self.margin_left = 20 * 2.834
        self.margin_right = 20 * 2.834
        self.content_width = 482
    
    def refresh_toko_info(self):
        """Refresh informasi toko dari database."""
        pengaturan = self.db.get_pengaturan()
        if pengaturan:
            self.nama_toko = pengaturan.get('nama_toko', 'PINGKAN STORE')
            self.alamat_toko = pengaturan.get('alamat_toko')
    
    def generate_qr_code_with_watermark(self, data, status):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = BytesIO()
        if qr_img.mode != 'RGB':
            qr_img = qr_img.convert('RGB')
        qr_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        return img_buffer
    
    def format_rupiah(self, amount):
        return f"Rp {amount:,}".replace(',', '.')
    
    def create_invoice(self, transaksi_id):
        """Generate invoice PDF dengan layout yang rapi dan konsisten"""
        # Refresh info toko terbaru
        self.refresh_toko_info()
        
        detail_data = self.db.get_transaksi_detail(transaksi_id)
        if not detail_data:
            return None
        
        transaksi = detail_data[0]
        nama_pembeli = transaksi[1]
        subtotal = transaksi[2]
        pembayaran = transaksi[3]
        status = transaksi[4]
        tanggal = transaksi[5]
        no_invoice = transaksi[6]
        sisa_pembayaran = subtotal - pembayaran
        
        folder = 'invoice/lunas' if status == 'LUNAS' else 'invoice/belum_lunas'
        safe_nama = nama_pembeli.replace(' ', '_').replace('/', '_')
        filename = f"{no_invoice}-{self.nama_toko}-{tanggal}-{safe_nama}.pdf"
        filepath = os.path.join(folder, filename)
        
        doc = CustomDocTemplate(filepath, pagesize=A4, status=status,
                              rightMargin=20*mm, leftMargin=20*mm,
                              topMargin=25*mm, bottomMargin=25*mm)
        
        styles = getSampleStyleSheet()
        
        company_style = ParagraphStyle(
            'CompanyStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#2E5BBA'),
            fontName='Helvetica-Bold',
            leading=15,
            alignment=TA_LEFT
        )
        
        invoice_info_style = ParagraphStyle(
            'InvoiceInfoStyle',
            parent=styles['Normal'],
            fontSize=11,
            textColor=colors.black,
            fontName='Helvetica',
            leading=15,
            alignment=TA_RIGHT
        )
        
        story = []
        story.append(DecorativeLine(width=self.content_width, style='double'))
        story.append(Spacer(1, 12))
        
        invoice_title_data = [["INVOICE"]]
        invoice_title_table = Table(invoice_title_data, colWidths=[self.content_width])
        invoice_title_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#2E5BBA')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 20),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(invoice_title_table)
        story.append(Spacer(1, 15))
        
        col_width = self.content_width / 2
        header_data = [[Paragraph(f"<b>{self.nama_toko}</b><br/>{self.alamat_toko}", company_style),
                       Paragraph(f"<b>Invoice No:</b> {no_invoice}<br/><b>Tanggal:</b> {datetime.strptime(tanggal, '%Y-%m-%d').strftime('%d %B %Y')}<br/><b>Pelanggan:</b> {nama_pembeli}", invoice_info_style)]]
        
        header_table = Table(header_data, colWidths=[col_width, col_width])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#2E5BBA')),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 15))
        story.append(DecorativeLine(width=self.content_width, style='solid'))
        story.append(Spacer(1, 12))
        
        table_data = [['No', 'Warna', 'Kategori', 'Ukuran', 'Qty', 'Harga Satuan', 'Total']]
        no = 1
        for item in detail_data:
            qty = item[7]
            harga = item[8]
            warna = item[9]
            kategori = item[10]
            ukuran = item[11]
            total = qty * harga
            table_data.append([str(no), warna, kategori, ukuran, str(qty), self.format_rupiah(harga), self.format_rupiah(total)])
            no += 1
        
        col_widths = [25, 70, 80, 55, 35, 106, 111]
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E5BBA')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F9FA')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#DDDDDD')),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 1), (3, -1), 'LEFT'),
            ('ALIGN', (4, 1), (6, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(table)
        story.append(Spacer(1, 15))
        
        qr_data = f"""{self.nama_toko}
INVOICE: {no_invoice}
Nama: {nama_pembeli}
Status: {status}
Subtotal: {self.format_rupiah(subtotal)}
Pembayaran: {self.format_rupiah(pembayaran)}
Sisa: {self.format_rupiah(sisa_pembayaran)}
Tanggal: {tanggal}"""
        
        qr_buffer = self.generate_qr_code_with_watermark(qr_data, status)
        qr_image = Image(qr_buffer, width=65, height=65)
        
        qr_section = Table([[qr_image], [Paragraph("Scan QR Code untuk<br/>verifikasi invoice", 
                  ParagraphStyle('QRLabel', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, leading=11))]], colWidths=[120])
        qr_section.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        summary_data = [['Subtotal:', self.format_rupiah(subtotal)], ['Sisa Pembayaran:', self.format_rupiah(sisa_pembayaran)], ['', ''], ['Pembayaran:', self.format_rupiah(pembayaran)]]
        summary_table = Table(summary_data, colWidths=[140, 120])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 2), 'Helvetica'),
            ('FONTNAME', (0, 3), (-1, 3), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 2), 11),
            ('FONTSIZE', (0, 3), (-1, 3), 12),
            ('LINEBELOW', (0, 3), (-1, 3), 2.5, colors.HexColor('#2E5BBA')),
            ('TEXTCOLOR', (0, 3), (-1, 3), colors.HexColor('#2E5BBA')),
        ]))
        
        spacer_section = Table([['']], colWidths=[142])
        spacer_section.setStyle(TableStyle([('TOPPADDING', (0, 0), (-1, -1), 0)]))
        
        bottom_section = Table([[qr_section, spacer_section, summary_table]], colWidths=[120, 142, 220])
        bottom_section.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ]))
        
        story.append(bottom_section)
        story.append(Spacer(1, 20))
        
        thanks_style = ParagraphStyle(
            'ThanksStyle',
            parent=styles['Normal'],
            fontSize=13,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2E5BBA'),
            fontName='Helvetica-Bold',
            leading=18
        )
        
        subthanks_style = ParagraphStyle(
            'SubThanksStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#666666'),
            leading=14
        )
        
        story.append(Paragraph("Terima kasih atas kepercayaan Anda!", thanks_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph("Semoga puas dengan produk dan layanan kami", subthanks_style))
        story.append(Spacer(1, 25))
        
        signature_data = [['', datetime.now().strftime('%d %B %Y')], ['', ''], ['', 'Hormat Kami,']]
        signature_table = Table(signature_data, colWidths=[320, 162])
        signature_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(signature_table)
        story.append(Spacer(1, 15))
        
        doc.build(story)
        return filepath
    
    def print_invoice(self, transaksi_id):
        try:
            filepath = self.create_invoice(transaksi_id)
            if filepath:
                print(f"Invoice berhasil dibuat: {filepath}")
                return filepath
            else:
                print("Gagal membuat invoice")
                return None
        except Exception as e:
            print(f"Error generating invoice: {str(e)}")
            return None