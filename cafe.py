import datetime
import json
import os
import re
import sys

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.lib import pagesizes
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
except ImportError:
    colors = None
    TA_CENTER = 1
    TA_RIGHT = 2
    pagesizes = None
    ParagraphStyle = None
    getSampleStyleSheet = None
    inch = 72
    Image = None
    Paragraph = None
    SimpleDocTemplate = None
    Spacer = None
    Table = None
    TableStyle = None


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MENU_FILE = os.path.join(BASE_DIR, "menu.json")
SALES_FILE = os.path.join(BASE_DIR, "sales.json")
ORDER_QUEUE_FILE = os.path.join(BASE_DIR, "orders.json")
LOGO_PATH = os.path.join(BASE_DIR, "logo_cafe.png")

WAITING_PAYMENT = "WAITING_PAYMENT"
PAID = "PAID"
CANCELLED = "CANCELLED"

USERS = {
    "admin": "1234",
    "kasir": "1234",
}

DEFAULT_MENU = {
    "Americano": 18000,
    "Cappuccino": 22000,
    "Cafe Latte": 23000,
    "Kopi Susu Gula Aren": 20000,
    "Espresso": 15000,
    "Macchiato": 24000,
    "Mocha": 25000,
    "Vanilla Latte": 26000,
    "Matcha Latte": 24000,
    "Chocolate": 21000,
    "Lemon Tea": 16000,
    "Lychee Tea": 18000,
    "Mineral Water": 8000,
    "Croissant": 18000,
    "French Fries": 17000,
    "Chicken Katsu Rice": 32000,
    "Nasi Goreng": 28000,
    "Spaghetti Bolognese": 30000,
    "Chicken Sandwich": 27000,
    "Cheesecake": 23000,
}


# ================= UTILITIES =================

def safe_input(prompt):
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print("\nKembali ke menu sebelumnya...")
        raise


def format_rupiah(n):
    return f"Rp{int(n):,}".replace(",", ".")


def now_string():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_datetime(value):
    text = str(value)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(text[:26], fmt)
        except ValueError:
            continue

    try:
        return datetime.datetime.fromisoformat(text)
    except ValueError:
        return datetime.datetime.min


def format_datetime_display(value):
    parsed = parse_datetime(value)
    if parsed == datetime.datetime.min:
        return str(value)
    return parsed.strftime("%d-%m-%Y %H:%M")


def parse_number(text):
    clean = re.sub(r"[^\d]", "", str(text))
    if clean == "":
        raise ValueError("Input harus berupa angka")
    return int(clean)


def load_json_file(path, default):
    try:
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return default

        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, type(default)):
            return data
        return default
    except (json.JSONDecodeError, OSError):
        return default


def save_json_file(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def wait_enter():
    try:
        safe_input("\nTekan Enter untuk lanjut...")
    except (EOFError, KeyboardInterrupt):
        pass


# ================= MENU MANAGER =================

class MenuManager:
    def __init__(self):
        self.menu = self.load()

    def load(self):
        menu = load_json_file(MENU_FILE, {})
        if not menu:
            menu = DEFAULT_MENU.copy()
            self.menu = menu
            self.save()
        return menu

    def save(self):
        save_json_file(MENU_FILE, self.menu)

    def show(self, menu_data=None, title="DAFTAR MENU"):
        menu_data = self.menu if menu_data is None else menu_data
        items = list(menu_data.items()) if isinstance(menu_data, dict) else list(menu_data)

        print(f"\n--- {title} ---")
        print("=" * 58)
        if not items:
            print("Belum ada menu")
        else:
            for index, (name, price) in enumerate(items, start=1):
                print(f"{index:>2}. {name:<32} {format_rupiah(price):>15}")
        print("=" * 58)

    def add(self):
        try:
            name = safe_input("Nama menu: ").strip().title()
            if not name:
                print("Nama menu tidak boleh kosong")
                return

            if name in self.menu:
                print(f"Menu {name} sudah ada dengan harga {format_rupiah(self.menu[name])}.")
                print("Gunakan Update Menu jika ingin mengubah harga menu.")
                return

            price = parse_number(safe_input("Harga: "))
            if price <= 0:
                print("Harga harus lebih dari 0")
                return

            self.menu[name] = price
            self.save()
            print("Menu ditambahkan")
        except (ValueError, EOFError, KeyboardInterrupt):
            print("Input tidak valid")

    def update(self):
        try:
            name = safe_input("Nama menu: ").strip().title()
            if name not in self.menu:
                print("Menu tidak ada")
                return

            price = parse_number(safe_input("Harga baru: "))
            if price <= 0:
                print("Harga harus lebih dari 0")
                return

            self.menu[name] = price
            self.save()
            print("Menu diperbarui")
        except (ValueError, EOFError, KeyboardInterrupt):
            print("Input tidak valid")

    def delete(self):
        try:
            self.show(title="DAFTAR MENU YANG TERSEDIA")
            name = safe_input("Nama menu: ").strip().title()
            if name not in self.menu:
                print("Menu tidak ada")
                return

            confirm = safe_input(f"Yakin hapus {name}? (y/n): ").strip().lower()
            if confirm != "y":
                print("Hapus menu dibatalkan")
                return

            del self.menu[name]
            self.save()
            print("Menu dihapus")
        except (EOFError, KeyboardInterrupt):
            print("Input tidak valid")

    def search_items(self, keyword):
        keyword = keyword.strip().lower()
        digits = re.sub(r"[^\d]", "", keyword)

        return {
            name: price
            for name, price in self.menu.items()
            if keyword in name.lower() or (digits and digits in str(price))
        }

    def search(self):
        try:
            keyword = safe_input("Cari menu berdasarkan nama/harga: ").strip()
            if not keyword:
                print("Kata kunci tidak boleh kosong")
                return {}

            result = self.search_items(keyword)
            if not result:
                print("Menu tidak ditemukan")
                return {}

            self.show(result, f"HASIL PENCARIAN: {keyword}")
            return result
        except (EOFError, KeyboardInterrupt):
            print("Kembali...")
            return {}

    def get_sorted_items(self, choice, menu_data=None):
        menu_data = self.menu if menu_data is None else menu_data
        items = list(menu_data.items()) if isinstance(menu_data, dict) else list(menu_data)

        if choice == "1":
            return sorted(items, key=lambda item: (item[1], item[0].lower()))
        if choice == "2":
            return sorted(items, key=lambda item: (item[1], item[0].lower()), reverse=True)
        if choice == "3":
            return sorted(items, key=lambda item: item[0].lower())
        if choice == "4":
            return sorted(items, key=lambda item: item[0].lower(), reverse=True)
        return None

    def sort_menu(self, menu_data=None):
        try:
            print("\n--- SORTING MENU ---")
            print("1. Harga Naik")
            print("2. Harga Turun")
            print("3. Nama A-Z")
            print("4. Nama Z-A")
            print("0. Kembali")

            choice = safe_input("Pilih: ").strip()
            if choice == "0":
                return []

            sorted_items = self.get_sorted_items(choice, menu_data)
            if sorted_items is None:
                print("Pilihan tidak valid")
                return []

            self.show(sorted_items, "HASIL SORTING")
            return sorted_items
        except (EOFError, KeyboardInterrupt):
            print("Kembali...")
            return []


# ================= PDF GENERATOR =================

class PDFGenerator:
    def is_available(self):
        return SimpleDocTemplate is not None

    def open_file(self, filename):
        try:
            os.startfile(filename)
        except OSError:
            print(f"File berhasil dibuat: {filename}")

    def get_pdf_styles(self):
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name="BrandTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#1F3A5F"),
            spaceAfter=4,
        ))
        styles.add(ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#1F3A5F"),
            spaceBefore=8,
            spaceAfter=8,
        ))
        styles.add(ParagraphStyle(
            name="SmallMuted",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#667085"),
        ))
        styles.add(ParagraphStyle(
            name="Right",
            parent=styles["Normal"],
            alignment=TA_RIGHT,
        ))
        styles.add(ParagraphStyle(
            name="CenterSmall",
            parent=styles["Normal"],
            alignment=TA_CENTER,
            fontSize=8,
            leading=10,
        ))
        return styles

    def build_item_rows(self, cart, include_number=True):
        rows = []
        for index, (name, item) in enumerate(cart.items(), start=1):
            qty = int(item[0]) if isinstance(item, (list, tuple)) and len(item) >= 1 else 1
            subtotal = int(item[1]) if isinstance(item, (list, tuple)) and len(item) >= 2 else 0
            unit_price = round(subtotal / qty) if qty else 0
            if include_number:
                rows.append([index, name, qty, format_rupiah(unit_price), format_rupiah(subtotal)])
            else:
                rows.append([name, qty, format_rupiah(unit_price), format_rupiah(subtotal)])
        return rows

    def generate_invoice(
        self,
        invoice_no,
        cart,
        total,
        discount,
        tax,
        grand_total,
        customer_name="-",
        order_no="-",
    ):
        if not self.is_available():
            print("ReportLab belum terinstall. Tidak bisa membuat PDF invoice.")
            return

        filename = os.path.join(BASE_DIR, f"Invoice_{invoice_no}.pdf")
        doc = SimpleDocTemplate(
            filename,
            pagesize=pagesizes.A4,
            rightMargin=42,
            leftMargin=42,
            topMargin=36,
            bottomMargin=36,
        )
        elements = []
        styles = self.get_pdf_styles()

        header_left = [
            Paragraph("CAFE ENTERPRISE", styles["BrandTitle"]),
            Paragraph("Jl. Aroma Kopi No. 11, Kota Kopi", styles["SmallMuted"]),
            Paragraph("Telp. 021-1100-CAFE | cafe.enterprise@example.com", styles["SmallMuted"]),
        ]
        header_right = [
            Paragraph("<b>INVOICE</b>", styles["Right"]),
            Paragraph(invoice_no, styles["Right"]),
            Paragraph(datetime.datetime.now().strftime("%d-%m-%Y %H:%M"), styles["Right"]),
        ]

        logo_or_text = header_left
        if os.path.exists(LOGO_PATH):
            try:
                logo_or_text = [Image(LOGO_PATH, width=0.75 * inch, height=0.75 * inch)] + header_left
            except Exception:
                logo_or_text = header_left

        header_table = Table([[logo_or_text, header_right]], colWidths=[320, 170])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ("LINEBELOW", (0, 0), (-1, -1), 1, colors.HexColor("#D0D5DD")),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 14))

        info_table = Table([
            ["No. Order", order_no, "Pelanggan", customer_name],
            ["No. Invoice", invoice_no, "Tanggal", datetime.datetime.now().strftime("%d-%m-%Y %H:%M")],
        ], colWidths=[82, 165, 82, 165])
        info_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2F4F7")),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#D0D5DD")),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D0D5DD")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#344054")),
            ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#344054")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 16))

        elements.append(Paragraph("Rincian Pesanan", styles["SectionTitle"]))
        item_data = [["No", "Menu", "Qty", "Harga", "Subtotal"]]
        item_data.extend(self.build_item_rows(cart))
        table = Table(item_data, colWidths=[36, 210, 48, 95, 105], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3A5F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D5DD")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ("ALIGN", (0, 1), (0, -1), "CENTER"),
            ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 14))

        summary_data = [
            ["Subtotal", format_rupiah(total)],
            ["Diskon", f"{discount}%"],
            ["Pajak 10%", format_rupiah(tax)],
            ["Grand Total", format_rupiah(grand_total)],
        ]
        summary_table = Table(summary_data, colWidths=[120, 130], hAlign="RIGHT")
        summary_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -2), "Helvetica"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#1F3A5F")),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EAF0F8")),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 24))
        elements.append(Paragraph("Terima kasih sudah berbelanja. Simpan invoice ini sebagai bukti pembayaran.", styles["CenterSmall"]))

        doc.build(elements)
        self.open_file(filename)

    def generate_receipt(self, invoice_no, cart, grand_total, customer_name="-", order_no="-"):
        if not self.is_available():
            print("ReportLab belum terinstall. Tidak bisa membuat PDF struk.")
            return

        filename = os.path.join(BASE_DIR, f"Struk_{invoice_no}.pdf")
        width = 226
        height = 800
        doc = SimpleDocTemplate(
            filename,
            pagesize=(width, height),
            rightMargin=12,
            leftMargin=12,
            topMargin=12,
            bottomMargin=12,
        )
        styles = self.get_pdf_styles()
        elements = [
            Paragraph("<b>CAFE ENTERPRISE</b>", styles["CenterSmall"]),
            Paragraph("Jl. Aroma Kopi No. 11", styles["CenterSmall"]),
            Paragraph("Telp. 021-1100-CAFE", styles["CenterSmall"]),
            Spacer(1, 10),
        ]

        meta_table = Table([
            ["Invoice", invoice_no],
            ["Order", order_no],
            ["Pelanggan", customer_name],
            ["Tanggal", datetime.datetime.now().strftime("%d-%m-%Y %H:%M")],
        ], colWidths=[58, 140])
        meta_table.setStyle(TableStyle([
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 8))

        subtotal_total = 0
        data = [["Item", "Qty", "Subtotal"]]
        for name, item in cart.items():
            qty = int(item[0]) if isinstance(item, (list, tuple)) and len(item) >= 1 else 1
            subtotal = int(item[1]) if isinstance(item, (list, tuple)) and len(item) >= 2 else 0
            subtotal_total += subtotal
            data.append([Paragraph(name, styles["SmallMuted"]), qty, format_rupiah(subtotal)])
        tax = int(grand_total) - subtotal_total
        data.append(["", "", ""])
        data.append(["Subtotal", "", format_rupiah(subtotal_total)])
        data.append(["Pajak", "", format_rupiah(tax)])
        data.append(["TOTAL", "", format_rupiah(grand_total)])

        table = Table(data, colWidths=[102, 30, 66])
        table.setStyle(TableStyle([
            ("LINEABOVE", (0, 0), (-1, 0), 0.6, colors.black),
            ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.black),
            ("LINEABOVE", (0, -3), (-1, -3), 0.6, colors.black),
            ("LINEABOVE", (0, -1), (-1, -1), 0.8, colors.black),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("Terima kasih", styles["CenterSmall"]))
        elements.append(Paragraph("Silakan datang kembali", styles["CenterSmall"]))

        doc.build(elements)
        self.open_file(filename)


# ================= ORDER MANAGER =================

class OrderManager:
    def __init__(self):
        self.orders = self.load()

    def load(self):
        if not os.path.exists(ORDER_QUEUE_FILE) or os.path.getsize(ORDER_QUEUE_FILE) == 0:
            save_json_file(ORDER_QUEUE_FILE, {})

        data = load_json_file(ORDER_QUEUE_FILE, {})
        if not isinstance(data, dict):
            data = {}
            save_json_file(ORDER_QUEUE_FILE, data)
        return data

    def save(self):
        save_json_file(ORDER_QUEUE_FILE, self.orders)

    def normalize_items(self, items):
        normalized = {}
        for name, item_data in items.items():
            if isinstance(item_data, (list, tuple)) and len(item_data) >= 2:
                qty = int(item_data[0])
                subtotal = int(item_data[1])
            else:
                qty = 1
                subtotal = int(item_data)
            normalized[name] = [qty, subtotal]
        return normalized

    def generate_order_no(self):
        max_number = 0
        for order_no in self.orders.keys():
            match = re.fullmatch(r"ORD(\d+)", str(order_no))
            if match:
                max_number = max(max_number, int(match.group(1)))
        return f"ORD{max_number + 1:04d}"

    def place_order(self, customer_name, items, subtotal, tax, grand_total):
        self.orders = self.load()
        order_no = self.generate_order_no()
        self.orders[order_no] = {
            "tanggal": now_string(),
            "customer_name": customer_name,
            "items": self.normalize_items(items),
            "subtotal": int(subtotal),
            "tax": int(tax),
            "grand_total": int(grand_total),
            "status": WAITING_PAYMENT,
        }
        self.save()
        return order_no

    def get_order(self, order_no):
        self.orders = self.load()
        return self.orders.get(str(order_no).strip().upper())

    def sort_orders_by_latest(self, orders):
        return sorted(
            orders,
            key=lambda item: parse_datetime(item[1].get("tanggal", "")),
            reverse=True,
        )

    def get_pending_orders(self):
        self.orders = self.load()
        pending = [
            (order_no, order)
            for order_no, order in self.orders.items()
            if order.get("status") == WAITING_PAYMENT
        ]
        return self.sort_orders_by_latest(pending)

    def get_all_orders_sorted(self, statuses=None):
        self.orders = self.load()
        status_filter = set(statuses) if statuses else None
        orders = [
            (order_no, order)
            for order_no, order in self.orders.items()
            if status_filter is None or order.get("status") in status_filter
        ]
        return self.sort_orders_by_latest(orders)

    def format_order_line(self, index, order_no, order):
        customer = order.get("customer_name", "-")
        total = format_rupiah(order.get("grand_total", 0))
        status = order.get("status", "-")
        tanggal = format_datetime_display(order.get("tanggal", "-"))
        return f"{index}. {order_no:<7} | {customer:<10} | {total:>10} | {status:<15} | {tanggal}"

    def show_order_detail(self, order_no, message_for=None):
        order_no = str(order_no).strip().upper()
        order = self.get_order(order_no)

        if not order:
            print("Order tidak ditemukan.")
            return None

        print("\n--- DETAIL ORDER ---")
        print(f"Nomor Order : {order_no}")
        print(f"Nama        : {order.get('customer_name', '-')}")
        print(f"Tanggal     : {format_datetime_display(order.get('tanggal', '-'))}")
        print("\nItem:")
        for name, item_data in order.get("items", {}).items():
            qty = item_data[0] if isinstance(item_data, (list, tuple)) and len(item_data) >= 1 else 1
            subtotal = item_data[1] if isinstance(item_data, (list, tuple)) and len(item_data) >= 2 else 0
            print(f"- {name:<30} x{qty:<3} {format_rupiah(subtotal):>12}")
        print("-" * 50)
        print(f"Subtotal    : {format_rupiah(order.get('subtotal', 0))}")
        print(f"Pajak 10%   : {format_rupiah(order.get('tax', 0))}")
        print(f"Grand Total : {format_rupiah(order.get('grand_total', 0))}")
        print(f"Status      : {order.get('status', '-')}")
        if order.get("invoice_no"):
            print(f"Invoice No  : {order['invoice_no']}")

        status = order.get("status")
        if message_for == "customer":
            if status == WAITING_PAYMENT:
                print("Silakan bayar di kasir.")
            elif status == PAID:
                print("Pembayaran sudah dikonfirmasi kasir.")
        elif message_for == "cashier":
            if status == WAITING_PAYMENT:
                print("Pesanan belum dibayar. Silakan konfirmasi pembayaran di menu kasir.")
            elif status == PAID:
                print("Pembayaran sudah dikonfirmasi.")

        return order

    def check_order_status(self, order_no):
        return self.show_order_detail(order_no, message_for="customer")

    def mark_paid(self, order_no, invoice_no):
        order_no = str(order_no).strip().upper()
        self.orders = self.load()
        if order_no not in self.orders:
            return False

        self.orders[order_no]["status"] = PAID
        self.orders[order_no]["invoice_no"] = invoice_no
        self.save()
        return True

    def mark_cancelled(self, order_no):
        order_no = str(order_no).strip().upper()
        self.orders = self.load()
        if order_no not in self.orders:
            return False

        self.orders[order_no]["status"] = CANCELLED
        self.save()
        return True


# ================= TRANSACTION =================

class TransactionManager:
    def __init__(self, menu_manager, order_manager):
        self.menu_manager = menu_manager
        self.order_manager = order_manager
        self.sales = self.load()
        self.pdf = PDFGenerator()

    def load(self):
        data = load_json_file(SALES_FILE, {})
        return data if isinstance(data, dict) else {}

    def save(self):
        save_json_file(SALES_FILE, self.sales)

    def generate_invoice_no(self):
        self.sales = self.load()
        max_number = 0
        for invoice_no in self.sales.keys():
            match = re.fullmatch(r"INV(\d+)", str(invoice_no))
            if match:
                max_number = max(max_number, int(match.group(1)))
        return f"INV{max_number + 1:04d}"

    def kasir_menu(self):
        while True:
            print("\n--- MENU KASIR ---")
            print("1. Konfirmasi Pembayaran Order")
            print("2. Cek Status Order")
            print("3. Laporan Bulanan")
            print("4. Dashboard Grafik")
            print("0. Logout")

            try:
                choice = safe_input("Pilih: ").strip()

                if choice == "1":
                    self.confirm_order_payment()
                elif choice == "2":
                    self.check_all_order_status()
                elif choice == "3":
                    self.generate_monthly_report()
                    wait_enter()
                elif choice == "4":
                    self.show_chart()
                    wait_enter()
                elif choice == "0":
                    break
                else:
                    print("Pilihan tidak valid")
            except (EOFError, KeyboardInterrupt):
                break

    def confirm_order_payment(self):
        pending_orders = self.order_manager.get_pending_orders()

        if not pending_orders:
            print("Tidak ada order yang menunggu pembayaran.")
            wait_enter()
            return

        print("\n--- KONFIRMASI PEMBAYARAN ORDER ---")
        for index, (order_no, order) in enumerate(pending_orders, start=1):
            print(self.order_manager.format_order_line(index, order_no, order))

        try:
            choice = parse_number(safe_input("Pilih nomor order: "))
        except (ValueError, EOFError, KeyboardInterrupt):
            print("Pilihan harus berupa angka")
            wait_enter()
            return

        if choice < 1 or choice > len(pending_orders):
            print("Nomor order tidak ada")
            wait_enter()
            return

        order_no, order = pending_orders[choice - 1]
        self.order_manager.show_order_detail(order_no)

        grand_total = int(order.get("grand_total", 0))
        try:
            pay = parse_number(safe_input("Nominal bayar: "))
        except (ValueError, EOFError, KeyboardInterrupt):
            print("Input pembayaran tidak valid")
            wait_enter()
            return

        if pay < grand_total:
            print("Uang bayar kurang. Pembayaran dibatalkan.")
            wait_enter()
            return

        print("Kembalian:", format_rupiah(pay - grand_total))
        try:
            confirm = safe_input("Konfirmasi pembayaran? (y/n): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("Pembayaran dibatalkan.")
            wait_enter()
            return

        if confirm != "y":
            print("Pembayaran dibatalkan.")
            wait_enter()
            return

        invoice_no = self.generate_invoice_no()
        cart = self.order_manager.normalize_items(order.get("items", {}))
        subtotal = int(order.get("subtotal", 0))
        tax = int(order.get("tax", 0))

        self.sales[invoice_no] = {
            "tanggal": now_string(),
            "items": cart,
            "total": grand_total,
        }
        self.save()
        self.order_manager.mark_paid(order_no, invoice_no)

        print("Pembayaran berhasil dikonfirmasi.")
        print(f"Order {order_no} menjadi PAID.")
        print(f"Invoice {invoice_no} berhasil dibuat.")

        print("\n--- CETAK ---")
        print("1. Invoice A4")
        print("2. Struk Thermal")
        print("0. Tidak Cetak")
        cetak = safe_input("Pilih cetak: ").strip()

        if cetak == "1":
            self.pdf.generate_invoice(
                invoice_no,
                cart,
                subtotal,
                0,
                tax,
                grand_total,
                customer_name=order.get("customer_name", "-"),
                order_no=order_no,
            )
        elif cetak == "2":
            self.pdf.generate_receipt(
                invoice_no,
                cart,
                grand_total,
                customer_name=order.get("customer_name", "-"),
                order_no=order_no,
            )

        wait_enter()

    def check_all_order_status(self):
        orders = self.order_manager.get_all_orders_sorted(statuses=[WAITING_PAYMENT, PAID])

        print("\n--- CEK STATUS ORDER ---")
        print("Menampilkan semua order dari yang paling baru\n")

        if not orders:
            print("Belum ada order.")
            wait_enter()
            return

        for index, (order_no, order) in enumerate(orders, start=1):
            print(self.order_manager.format_order_line(index, order_no, order))

        while True:
            print("\n1. Lihat Detail Order")
            print("0. Kembali")

            try:
                choice = safe_input("Pilih: ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if choice == "1":
                order_no = safe_input("Nomor order: ").strip().upper()
                self.order_manager.show_order_detail(order_no, message_for="cashier")
                wait_enter()
            elif choice == "0":
                break
            else:
                print("Pilihan tidak valid")

    def generate_monthly_report(self):
        self.sales = self.load()
        if not self.pdf.is_available():
            print("ReportLab belum terinstall. Tidak bisa membuat laporan PDF.")
            return

        filename = os.path.join(BASE_DIR, "Laporan_Bulanan.pdf")
        doc = SimpleDocTemplate(
            filename,
            pagesize=pagesizes.A4,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        elements = []
        styles = self.pdf.get_pdf_styles()

        sales_items = sorted(
            self.sales.items(),
            key=lambda item: parse_datetime(item[1].get("tanggal", "")),
            reverse=True,
        )
        total_income = sum(int(sale.get("total", 0)) for _, sale in sales_items)
        average_income = round(total_income / len(sales_items)) if sales_items else 0

        item_count = {}
        for _, sale in sales_items:
            for item_name, item_data in sale.get("items", {}).items():
                qty = item_data[0] if isinstance(item_data, (list, tuple)) and len(item_data) >= 1 else 1
                item_count[item_name] = item_count.get(item_name, 0) + int(qty)

        elements.append(Paragraph("LAPORAN PENJUALAN BULANAN", styles["BrandTitle"]))
        elements.append(Paragraph(
            f"Dibuat pada {datetime.datetime.now().strftime('%d-%m-%Y %H:%M')} | Sumber data: sales.json",
            styles["SmallMuted"],
        ))
        elements.append(Spacer(1, 14))

        summary_table = Table([
            ["Total Transaksi", str(len(sales_items)), "Total Pendapatan", format_rupiah(total_income)],
            ["Rata-rata Transaksi", format_rupiah(average_income), "Jumlah Menu Terjual", str(sum(item_count.values()))],
        ], colWidths=[118, 112, 128, 155])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2F4F7")),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#D0D5DD")),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D0D5DD")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 16))

        elements.append(Paragraph("Menu Terlaris", styles["SectionTitle"]))
        top_items = sorted(item_count.items(), key=lambda item: item[1], reverse=True)[:5]
        top_data = [["No", "Menu", "Qty Terjual"]]
        if top_items:
            for index, (item_name, qty) in enumerate(top_items, start=1):
                top_data.append([index, item_name, qty])
        else:
            top_data.append(["-", "Belum ada data", 0])

        top_table = Table(top_data, colWidths=[40, 350, 120])
        top_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3A5F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D5DD")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ("ALIGN", (0, 1), (0, -1), "CENTER"),
            ("ALIGN", (2, 1), (2, -1), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(top_table)
        elements.append(Spacer(1, 16))

        elements.append(Paragraph("Detail Penjualan", styles["SectionTitle"]))
        detail_data = [["No", "Invoice", "Tanggal", "Item Terjual", "Total"]]
        for index, (inv, sale) in enumerate(sales_items, start=1):
            total = int(sale.get("total", 0))
            item_text = []
            for item_name, item_data in sale.get("items", {}).items():
                qty = item_data[0] if isinstance(item_data, (list, tuple)) and len(item_data) >= 1 else 1
                item_text.append(f"{item_name} x{qty}")
            detail_data.append([
                index,
                inv,
                format_datetime_display(sale.get("tanggal", "")),
                Paragraph(", ".join(item_text) if item_text else "-", styles["SmallMuted"]),
                format_rupiah(total),
            ])

        if not sales_items:
            detail_data.append(["-", "-", "-", "Belum ada penjualan", format_rupiah(0)])

        detail_table = Table(detail_data, colWidths=[32, 74, 94, 220, 96], repeatRows=1)
        detail_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3A5F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D0D5DD")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ("ALIGN", (0, 1), (0, -1), "CENTER"),
            ("ALIGN", (4, 1), (4, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(detail_table)
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            "Catatan: laporan hanya menghitung transaksi yang sudah masuk sales.json.",
            styles["SmallMuted"],
        ))

        doc.build(elements)
        self.pdf.open_file(filename)

    def show_chart(self):
        self.sales = self.load()
        if plt is None:
            print("Matplotlib belum terinstall. Tidak bisa menampilkan grafik.")
            return

        item_count = {}
        for sale in self.sales.values():
            for item_name, item_data in sale.get("items", {}).items():
                qty = item_data[0] if isinstance(item_data, (list, tuple)) and len(item_data) >= 1 else 1
                item_count[item_name] = item_count.get(item_name, 0) + qty

        if not item_count:
            print("Belum ada data")
            return

        plt.figure()
        plt.bar(item_count.keys(), item_count.values())
        plt.xticks(rotation=45)
        plt.title("Menu Terlaris")
        plt.tight_layout()
        plt.show()


# ================= MAIN =================

class CafeSystem:
    def __init__(self):
        self.menu_manager = MenuManager()
        self.order_manager = OrderManager()
        self.transaction_manager = TransactionManager(self.menu_manager, self.order_manager)

    def login(self):
        while True:
            try:
                print("\n=== LOGIN KARYAWAN ===")
                user = safe_input("Username: ").strip().lower()
                pw = safe_input("Password: ").strip()
                if user in USERS and USERS[user] == pw:
                    return user
                print("Login salah")
            except (EOFError, KeyboardInterrupt):
                sys.exit()

    def run(self):
        while True:
            print("\n--- CAFE SYSTEM ---")
            print("1. Karyawan")
            print("2. Pelanggan")
            print("0. Keluar")

            try:
                choice = safe_input("Pilih: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("Program selesai.")
                break

            if choice == "1":
                user = self.login()
                if user == "admin":
                    self.admin_menu()
                elif user == "kasir":
                    self.transaction_manager.kasir_menu()
            elif choice == "2":
                self.customer_menu()
            elif choice == "0":
                print("Program selesai.")
                break
            else:
                print("Pilihan tidak valid")

    def admin_menu(self):
        while True:
            print("\n--- MENU ADMIN ---")
            print("1. Lihat Menu")
            print("2. Tambah Menu")
            print("3. Update Menu")
            print("4. Hapus Menu")
            print("5. Laporan Bulanan")
            print("6. Dashboard Grafik")
            print("0. Logout")

            try:
                choice = safe_input("Pilih: ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if choice == "1":
                self.admin_view_menu()
            elif choice == "2":
                self.menu_manager.add()
                wait_enter()
            elif choice == "3":
                self.menu_manager.update()
                wait_enter()
            elif choice == "4":
                self.menu_manager.delete()
                wait_enter()
            elif choice == "5":
                self.transaction_manager.generate_monthly_report()
                wait_enter()
            elif choice == "6":
                self.transaction_manager.show_chart()
                wait_enter()
            elif choice == "0":
                break
            else:
                print("Pilihan tidak valid")

    def admin_view_menu(self):
        active_items = list(self.menu_manager.menu.items())

        while True:
            self.menu_manager.show(active_items)
            print("\n--- AKSI LIHAT MENU ---")
            print("1. Search Menu")
            print("2. Sorting Menu")
            print("0. Kembali")

            try:
                choice = safe_input("Pilih: ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if choice == "1":
                keyword = safe_input("Cari menu berdasarkan nama/harga: ").strip()
                if not keyword:
                    print("Kata kunci tidak boleh kosong")
                    continue

                result = self.menu_manager.search_items(keyword)
                if not result:
                    print("Menu tidak ditemukan")
                else:
                    active_items = list(result.items())
            elif choice == "2":
                sorted_items = self.menu_manager.sort_menu(active_items)
                if sorted_items:
                    active_items = sorted_items
            elif choice == "0":
                break
            else:
                print("Pilihan tidak valid")

    def customer_menu(self):
        while True:
            print("\n--- MENU PELANGGAN ---")
            print("1. Order")
            print("2. Cek Status Order")
            print("0. Kembali")

            try:
                choice = safe_input("Pilih: ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if choice == "1":
                self.customer_order()
            elif choice == "2":
                self.customer_check_status()
            elif choice == "0":
                break
            else:
                print("Pilihan tidak valid")

    def calculate_cart_totals(self, cart):
        subtotal = sum(item[1] for item in cart.values())
        tax = round(subtotal * 0.10)
        grand_total = subtotal + tax
        return subtotal, tax, grand_total

    def show_cart(self, cart):
        print("\n--- KERANJANG ---")
        if not cart:
            print("Keranjang masih kosong")
            return

        for name, item in cart.items():
            print(f"{name:<30} x{item[0]:<3} {format_rupiah(item[1]):>12}")

        subtotal, tax, grand_total = self.calculate_cart_totals(cart)
        print("-" * 50)
        print(f"Subtotal    : {format_rupiah(subtotal)}")
        print(f"Pajak 10%   : {format_rupiah(tax)}")
        print(f"Grand Total : {format_rupiah(grand_total)}")

    def show_order_summary(self, customer_name, cart):
        subtotal, tax, grand_total = self.calculate_cart_totals(cart)
        print("\n--- RINGKASAN ORDER ---")
        print(f"Nama pelanggan: {customer_name}")
        for name, item in cart.items():
            print(f"- {name:<30} x{item[0]:<3} {format_rupiah(item[1]):>12}")
        print("-" * 50)
        print(f"Subtotal    : {format_rupiah(subtotal)}")
        print(f"Pajak 10%   : {format_rupiah(tax)}")
        print(f"Grand Total : {format_rupiah(grand_total)}")
        return subtotal, tax, grand_total

    def customer_order(self):
        try:
            customer_name = safe_input("Nama pelanggan: ").strip()
        except (EOFError, KeyboardInterrupt):
            return

        if not customer_name:
            print("Nama pelanggan tidak boleh kosong")
            wait_enter()
            return

        active_items = list(self.menu_manager.menu.items())
        cart = {}

        while True:
            self.menu_manager.show(active_items)
            print("\n--- AKSI ORDER ---")
            print("1. Pilih Menu")
            print("2. Search Menu")
            print("3. Sorting Menu")
            print("4. Lihat Keranjang")
            print("5. Checkout")
            print("0. Batal Order")

            try:
                choice = safe_input("Pilih: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("Order dibatalkan.")
                break

            if choice == "1":
                self.customer_pick_menu(active_items, cart)
            elif choice == "2":
                keyword = safe_input("Cari menu berdasarkan nama/harga: ").strip()
                if not keyword:
                    print("Kata kunci tidak boleh kosong")
                    continue

                result = self.menu_manager.search_items(keyword)
                if not result:
                    print("Menu tidak ditemukan")
                else:
                    active_items = list(result.items())
            elif choice == "3":
                sorted_items = self.menu_manager.sort_menu(active_items)
                if sorted_items:
                    active_items = sorted_items
            elif choice == "4":
                self.show_cart(cart)
                wait_enter()
            elif choice == "5":
                if self.checkout_customer_order(customer_name, cart):
                    break
            elif choice == "0":
                print("Order dibatalkan.")
                wait_enter()
                break
            else:
                print("Pilihan tidak valid")

    def customer_pick_menu(self, active_items, cart):
        if not active_items:
            print("Tidak ada menu yang bisa dipilih")
            return

        try:
            menu_index = parse_number(safe_input("Nomor menu: "))
            if menu_index < 1 or menu_index > len(active_items):
                print("Nomor menu tidak ada")
                return

            qty = parse_number(safe_input("Quantity: "))
            if qty <= 0:
                print("Quantity harus angka dan lebih dari 0")
                return
        except (ValueError, EOFError, KeyboardInterrupt):
            print("Input tidak valid")
            return

        name, price = active_items[menu_index - 1]
        subtotal = price * qty
        if name in cart:
            old_qty, old_subtotal = cart[name]
            cart[name] = [old_qty + qty, old_subtotal + subtotal]
        else:
            cart[name] = [qty, subtotal]

        print(f"{name} x{qty} masuk keranjang")

    def checkout_customer_order(self, customer_name, cart):
        if not cart:
            print("Keranjang masih kosong")
            return False

        subtotal, tax, grand_total = self.show_order_summary(customer_name, cart)

        try:
            confirm = safe_input("Konfirmasi checkout? (y/n): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return False

        if confirm == "y":
            order_no = self.order_manager.place_order(customer_name, cart, subtotal, tax, grand_total)
            print("Order berhasil dibuat.")
            print(f"Nomor order kamu: {order_no}")
            print("Silakan bayar di kasir.")
            wait_enter()
            return True

        if confirm == "n":
            return False

        print("Pilihan tidak valid")
        return False

    def customer_check_status(self):
        try:
            order_no = safe_input("Nomor order: ").strip().upper()
        except (EOFError, KeyboardInterrupt):
            return

        self.order_manager.check_order_status(order_no)
        wait_enter()


if __name__ == "__main__":
    CafeSystem().run()
