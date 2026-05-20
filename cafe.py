import datetime
import difflib
import json
import os
import re
import sys
import tempfile
import time

APP_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "baytul_cave_matplotlib"))

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


BASE_DIR = APP_DIR
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

BRAND_NAME = "BAYTUL CAFE"
BRAND_SUBTEXT = "PT RUMAH RAFLI"
BRAND_BLUE = "#0B63CE"
BRAND_NAVY = "#123B68"

ANSI_ENABLED = not os.environ.get("NO_COLOR")
ANSI = {
    "reset": "\033[0m",
    "blue": "\033[94m",
    "cyan": "\033[96m",
    "bold": "\033[1m",
    "muted": "\033[90m",
}


# ================= UTILITIES =================

def color_text(text, *styles):
    if not ANSI_ENABLED:
        return str(text)
    prefix = "".join(ANSI.get(style, "") for style in styles)
    return f"{prefix}{text}{ANSI['reset']}" if prefix else str(text)


def hacker_typing(text, delay=0.028, style="cyan", newline=True):
    if not sys.stdout.isatty():
        print(color_text(text, style, "bold"), end="\n" if newline else "")
        return

    for char in str(text):
        sys.stdout.write(color_text(char, style, "bold"))
        sys.stdout.flush()
        time.sleep(delay)
    if newline:
        print()


def print_header(title, subtitle=None, width=64):
    title = str(title).upper()
    line = "=" * width
    print()
    print(color_text(line, "blue", "bold"))
    print(color_text(title.center(width), "cyan", "bold"))
    if subtitle:
        print(color_text(str(subtitle).center(width), "muted"))
    print(color_text(line, "blue", "bold"))


def print_menu_options(title, options):
    print_header(title)
    for key, label in options:
        print(color_text(f"[{key}]", "cyan", "bold"), label)


def print_table(title, headers, rows, widths, align_right=None):
    align_right = set(align_right or [])
    print_header(title, width=sum(widths) + (3 * (len(widths) - 1)))
    header = " | ".join(str(value).ljust(widths[index]) for index, value in enumerate(headers))
    print(color_text(header, "blue", "bold"))
    print(color_text("-" * len(header), "blue"))

    if not rows:
        print("Belum ada data".center(len(header)))
        print(color_text("-" * len(header), "blue"))
        return

    for row in rows:
        cells = []
        for index, value in enumerate(row):
            text = str(value)
            if len(text) > widths[index]:
                text = text[: widths[index] - 3] + "..."
            cells.append(text.rjust(widths[index]) if index in align_right else text.ljust(widths[index]))
        print(" | ".join(cells))
    print(color_text("-" * len(header), "blue"))


def normalize_key(text):
    return re.sub(r"[^a-z0-9]+", "", str(text).lower())


def suggest_closest(value, choices, cutoff=0.55):
    if not value or not choices:
        return None

    lookup = {normalize_key(choice): choice for choice in choices}
    match = difflib.get_close_matches(normalize_key(value), lookup.keys(), n=1, cutoff=cutoff)
    return lookup[match[0]] if match else None


def show_suggestion(value, choices, label="input"):
    suggestion = suggest_closest(value, choices)
    if suggestion:
        print(color_text(f"Mungkin maksud Anda: {suggestion}", "cyan", "bold"))
    else:
        print(color_text(f"{label} tidak dikenali. Cek kembali tulisan atau pilih dari daftar.", "muted"))
    return suggestion


def prompt_menu_choice(prompt, options):
    keys = [str(key) for key, _ in options]
    labels = [str(label) for _, label in options]
    label_to_key = {normalize_key(label): str(key) for key, label in options}

    while True:
        choice = safe_input(prompt).strip()
        if choice in keys:
            return choice

        normalized = normalize_key(choice)
        if normalized in label_to_key:
            return label_to_key[normalized]

        suggestion = suggest_closest(choice, labels, cutoff=0.45)
        if suggestion:
            key = label_to_key[normalize_key(suggestion)]
            print(color_text(f"Mungkin maksud Anda: {suggestion} (pilihan {key})", "cyan", "bold"))
            continue

        show_suggestion(choice, keys, "Pilihan")


def prompt_confirm(prompt):
    yes_values = {"y", "ya", "yes", "iya"}
    no_values = {"n", "no", "tidak", "ga", "gak"}
    while True:
        answer = safe_input(prompt).strip().lower()
        if answer in yes_values:
            return True
        if answer in no_values:
            return False
        show_suggestion(answer, list(yes_values | no_values), "Konfirmasi")


def prompt_number(prompt, min_value=None, max_value=None):
    while True:
        try:
            value = parse_number(safe_input(prompt))
        except ValueError:
            print(color_text("Input harus berupa angka. Contoh: 1 atau 25000.", "muted"))
            continue

        if min_value is not None and value < min_value:
            print(color_text(f"Angka minimal {min_value}.", "muted"))
            continue
        if max_value is not None and value > max_value:
            print(color_text(f"Angka maksimal {max_value}.", "muted"))
            continue
        return value


def prompt_existing_name(prompt, choices, empty_message="Input tidak boleh kosong"):
    while True:
        value = safe_input(prompt).strip()
        if not value:
            print(empty_message)
            return None

        exact_lookup = {name.lower(): name for name in choices}
        if value.lower() in exact_lookup:
            return exact_lookup[value.lower()]

        title_value = value.title()
        if title_value in choices:
            return title_value

        show_suggestion(value, choices, "Nama")
        return None


DAY_NAMES = {
    0: "Senin",
    1: "Selasa",
    2: "Rabu",
    3: "Kamis",
    4: "Jumat",
    5: "Sabtu",
    6: "Minggu",
}

MONTH_NAMES = {
    1: "Januari",
    2: "Februari",
    3: "Maret",
    4: "April",
    5: "Mei",
    6: "Juni",
    7: "Juli",
    8: "Agustus",
    9: "September",
    10: "Oktober",
    11: "November",
    12: "Desember",
}


def format_realtime_history(value=None):
    parsed = datetime.datetime.now() if value is None else parse_datetime(value)
    if parsed == datetime.datetime.min:
        parsed = datetime.datetime.now()

    day = DAY_NAMES[parsed.weekday()]
    month = MONTH_NAMES[parsed.month]
    return {
        "hari": day,
        "tanggal": f"{parsed.day:02d} {month} {parsed.year}",
        "jam": parsed.strftime("%H:%M:%S"),
        "full": f"{day}, {parsed.day:02d} {month} {parsed.year} {parsed.strftime('%H:%M:%S')}",
    }


def get_sales_item_counts():
    sales = load_json_file(SALES_FILE, {})
    counts = {}
    if not isinstance(sales, dict):
        return counts

    for sale in sales.values():
        if not isinstance(sale, dict):
            continue
        for item_name, item_data in sale.get("items", {}).items():
            qty = item_data[0] if isinstance(item_data, (list, tuple)) and len(item_data) >= 1 else 1
            try:
                counts[item_name] = counts.get(item_name, 0) + int(qty)
            except (TypeError, ValueError):
                continue
    return counts


def get_top_menu_items(limit=5):
    counts = get_sales_item_counts()
    return sorted(counts.items(), key=lambda item: (-item[1], item[0].lower()))[:limit]


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
        return load_json_file(MENU_FILE, {})

    def save(self):
        save_json_file(MENU_FILE, self.menu)

    def show(self, menu_data=None, title="DAFTAR MENU"):
        menu_data = self.menu if menu_data is None else menu_data
        items = list(menu_data.items()) if isinstance(menu_data, dict) else list(menu_data)
        item_counts = get_sales_item_counts()
        top_items = get_top_menu_items(5)
        top_rank = {name: index for index, (name, _) in enumerate(top_items, start=1)}

        rows = []
        for index, (name, price) in enumerate(items, start=1):
            rank = top_rank.get(name)
            badge = "PALING LARIS" if rank == 1 else (f"TOP {rank}" if rank else "-")
            rows.append([
                index,
                name,
                format_rupiah(price),
                item_counts.get(name, 0),
                badge,
            ])

        print_table(
            title,
            ["No", "Menu", "Harga", "Terjual", "Status"],
            rows,
            [4, 30, 14, 8, 13],
            align_right={0, 2, 3},
        )

        if top_items:
            print(color_text("Menu paling banyak dipesan customer:", "cyan", "bold"))
            for rank, (name, qty) in enumerate(top_items, start=1):
                price = self.menu.get(name)
                price_text = format_rupiah(price) if price is not None else "Tidak ada di menu"
                print(f"{rank:>2}. {name:<30} {qty:>4} terjual | {price_text}")
        else:
            print(color_text("Menu terlaris belum tersedia karena belum ada data sales.", "muted"))

    def add(self):
        try:
            raw_name = safe_input("Nama menu: ").strip()
            name = raw_name.title()
            if not name:
                print("Nama menu tidak boleh kosong")
                return

            if name in self.menu:
                print(f"Menu {name} sudah ada dengan harga {format_rupiah(self.menu[name])}.")
                print("Gunakan Update Menu jika ingin mengubah harga menu.")
                return

            suggestion = suggest_closest(raw_name, self.menu.keys())
            if suggestion:
                print(color_text(f"Mungkin maksud Anda menu yang sudah ada: {suggestion}", "cyan", "bold"))
                if not prompt_confirm("Tetap tambah sebagai menu baru? (y/n): "):
                    print("Tambah menu dibatalkan.")
                    return

            price = prompt_number("Harga: ", min_value=1)
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
            name = prompt_existing_name("Nama menu: ", list(self.menu.keys()))
            if not name:
                return

            price = prompt_number("Harga baru: ", min_value=1)

            self.menu[name] = price
            self.save()
            print("Menu diperbarui")
        except (ValueError, EOFError, KeyboardInterrupt):
            print("Input tidak valid")

    def delete(self):
        try:
            self.show(title="DAFTAR MENU YANG TERSEDIA")
            name = prompt_existing_name("Nama menu: ", list(self.menu.keys()))
            if not name:
                return

            if not prompt_confirm(f"Yakin hapus {name}? (y/n): "):
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
            options = [
                ("1", "Harga Naik"),
                ("2", "Harga Turun"),
                ("3", "Nama A-Z"),
                ("4", "Nama Z-A"),
                ("0", "Kembali"),
            ]
            print_menu_options("SORTING MENU", options)

            choice = prompt_menu_choice("Pilih: ", options)
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
            textColor=colors.HexColor(BRAND_BLUE),
            spaceAfter=4,
        ))
        styles.add(ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor(BRAND_NAVY),
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
            Paragraph(BRAND_NAME, styles["BrandTitle"]),
            Paragraph(BRAND_SUBTEXT, styles["SmallMuted"]),
            Paragraph("Coffee, Eatery, and Cashier System", styles["SmallMuted"]),
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
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND_NAVY)),
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
            ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor(BRAND_NAVY)),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EAF3FF")),
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
            Paragraph(f"<b>{BRAND_NAME}</b>", styles["CenterSmall"]),
            Paragraph(BRAND_SUBTEXT, styles["CenterSmall"]),
            Paragraph("Coffee, Eatery, and Cashier System", styles["CenterSmall"]),
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

    def suggest_order_no(self, order_no):
        self.orders = self.load()
        return suggest_closest(str(order_no).strip().upper(), self.orders.keys(), cutoff=0.45)

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
            suggestion = self.suggest_order_no(order_no)
            if suggestion:
                print(color_text(f"Mungkin maksud Anda: {suggestion}", "cyan", "bold"))
            return None

        print_header("DETAIL ORDER")
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
            options = [
                ("1", "Konfirmasi Pembayaran Order"),
                ("2", "Cek Status Order"),
                ("3", "Laporan Bulanan"),
                ("4", "Dashboard Grafik"),
                ("5", "Riwayat Transaksi"),
                ("0", "Logout"),
            ]
            print_menu_options("MENU KASIR", options)

            try:
                choice = prompt_menu_choice("Pilih: ", options)

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
                elif choice == "5":
                    self.show_transaction_history()
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
            choice = prompt_number("Pilih nomor order: ", min_value=1, max_value=len(pending_orders))
        except (ValueError, EOFError, KeyboardInterrupt):
            print("Pilihan harus berupa angka")
            wait_enter()
            return

        order_no, order = pending_orders[choice - 1]
        self.order_manager.show_order_detail(order_no)

        grand_total = int(order.get("grand_total", 0))
        try:
            pay = prompt_number("Nominal bayar: ", min_value=0)
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
            confirm = prompt_confirm("Konfirmasi pembayaran? (y/n): ")
        except (EOFError, KeyboardInterrupt):
            print("Pembayaran dibatalkan.")
            wait_enter()
            return

        if not confirm:
            print("Pembayaran dibatalkan.")
            wait_enter()
            return

        invoice_no = self.generate_invoice_no()
        cart = self.order_manager.normalize_items(order.get("items", {}))
        subtotal = int(order.get("subtotal", 0))
        tax = int(order.get("tax", 0))
        paid_at = now_string()
        history_time = format_realtime_history(paid_at)

        self.sales[invoice_no] = {
            "tanggal": paid_at,
            "hari": history_time["hari"],
            "tanggal_lengkap": history_time["tanggal"],
            "jam": history_time["jam"],
            "order_no": order_no,
            "customer_name": order.get("customer_name", "-"),
            "items": cart,
            "total": grand_total,
        }
        self.save()
        self.order_manager.mark_paid(order_no, invoice_no)

        print("Pembayaran berhasil dikonfirmasi.")
        print(f"Order {order_no} menjadi PAID.")
        print(f"Invoice {invoice_no} berhasil dibuat.")
        print(color_text(f"Riwayat transaksi: {history_time['full']}", "cyan", "bold"))

        options = [
            ("1", "Invoice A4"),
            ("2", "Struk Thermal"),
            ("0", "Tidak Cetak"),
        ]
        print_menu_options("CETAK", options)
        cetak = prompt_menu_choice("Pilih cetak: ", options)

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
            options = [
                ("1", "Lihat Detail Order"),
                ("0", "Kembali"),
            ]
            print_menu_options("AKSI STATUS ORDER", options)

            try:
                choice = prompt_menu_choice("Pilih: ", options)
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

    def show_transaction_history(self):
        self.sales = self.load()
        self.order_manager.orders = self.order_manager.load()
        sales_items = sorted(
            self.sales.items(),
            key=lambda item: parse_datetime(item[1].get("tanggal", "")),
            reverse=True,
        )

        rows = []
        for index, (invoice_no, sale) in enumerate(sales_items, start=1):
            history_time = format_realtime_history(sale.get("tanggal", ""))
            order_no = sale.get("order_no", "-")
            customer = sale.get("customer_name", "-")
            if order_no == "-" or customer == "-":
                for saved_order_no, order in self.order_manager.orders.items():
                    if order.get("invoice_no") == invoice_no:
                        order_no = saved_order_no
                        customer = order.get("customer_name", "-")
                        break

            rows.append([
                index,
                invoice_no,
                order_no,
                customer,
                history_time["hari"],
                history_time["tanggal"],
                history_time["jam"],
                format_rupiah(sale.get("total", 0)),
            ])

        print_table(
            "RIWAYAT TRANSAKSI REALTIME",
            ["No", "Invoice", "Order", "Customer", "Hari", "Tanggal", "Jam", "Total"],
            rows,
            [4, 10, 9, 16, 8, 17, 9, 14],
            align_right={0, 7},
        )

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

        elements.append(Paragraph(f"{BRAND_NAME} - LAPORAN PENJUALAN BULANAN", styles["BrandTitle"]))
        elements.append(Paragraph(
            f"{BRAND_SUBTEXT} | Dibuat pada {datetime.datetime.now().strftime('%d-%m-%Y %H:%M')} | Sumber data: sales.json",
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
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND_NAVY)),
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
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND_NAVY)),
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
        plt.bar(item_count.keys(), item_count.values(), color=BRAND_BLUE)
        plt.xticks(rotation=45)
        plt.title(f"{BRAND_NAME} - Menu Terlaris")
        plt.tight_layout()
        plt.show()


# ================= MAIN =================

class CafeSystem:
    def __init__(self):
        self.menu_manager = MenuManager()
        self.order_manager = OrderManager()
        self.transaction_manager = TransactionManager(self.menu_manager, self.order_manager)
        self.banner_shown = False

    def login(self):
        while True:
            try:
                print_header("LOGIN KARYAWAN", BRAND_SUBTEXT)
                user = safe_input("Username: ").strip().lower()
                pw = safe_input("Password: ").strip()
                if user in USERS and USERS[user] == pw:
                    return user
                print("Login salah")
                show_suggestion(user, USERS.keys(), "Username")
            except (EOFError, KeyboardInterrupt):
                sys.exit()

    def run(self):
        if not self.banner_shown:
            hacker_typing(f"Initializing {BRAND_NAME} system...")
            hacker_typing("Loading customer favorites, cashier queue, and blue terminal UI...")
            print_header(BRAND_NAME, BRAND_SUBTEXT)
            self.banner_shown = True

        while True:
            options = [
                ("1", "Karyawan"),
                ("2", "Pelanggan"),
                ("0", "Keluar"),
            ]
            print_menu_options(f"{BRAND_NAME} SYSTEM", options)

            try:
                choice = prompt_menu_choice("Pilih: ", options)
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
            options = [
                ("1", "Lihat Menu"),
                ("2", "Tambah Menu"),
                ("3", "Update Menu"),
                ("4", "Hapus Menu"),
                ("5", "Laporan Bulanan"),
                ("6", "Dashboard Grafik"),
                ("7", "Riwayat Transaksi"),
                ("0", "Logout"),
            ]
            print_menu_options("MENU ADMIN", options)

            try:
                choice = prompt_menu_choice("Pilih: ", options)
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
            elif choice == "7":
                self.transaction_manager.show_transaction_history()
                wait_enter()
            elif choice == "0":
                break
            else:
                print("Pilihan tidak valid")

    def admin_view_menu(self):
        active_items = list(self.menu_manager.menu.items())

        while True:
            self.menu_manager.show(active_items)
            options = [
                ("1", "Search Menu"),
                ("2", "Sorting Menu"),
                ("0", "Kembali"),
            ]
            print_menu_options("AKSI LIHAT MENU", options)

            try:
                choice = prompt_menu_choice("Pilih: ", options)
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
                    show_suggestion(keyword, self.menu_manager.menu.keys(), "Menu")
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
            options = [
                ("1", "Order"),
                ("2", "Cek Status Order"),
                ("0", "Kembali"),
            ]
            print_menu_options("MENU PELANGGAN", options)

            try:
                choice = prompt_menu_choice("Pilih: ", options)
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
        print_header("KERANJANG")
        if not cart:
            print("Keranjang masih kosong")
            return

        rows = [
            [index, name, item[0], format_rupiah(item[1])]
            for index, (name, item) in enumerate(cart.items(), start=1)
        ]
        print_table("ISI KERANJANG", ["No", "Menu", "Qty", "Subtotal"], rows, [4, 30, 6, 14], align_right={0, 2, 3})

        subtotal, tax, grand_total = self.calculate_cart_totals(cart)
        print("-" * 50)
        print(f"Subtotal    : {format_rupiah(subtotal)}")
        print(f"Pajak 10%   : {format_rupiah(tax)}")
        print(f"Grand Total : {format_rupiah(grand_total)}")

    def show_order_summary(self, customer_name, cart):
        subtotal, tax, grand_total = self.calculate_cart_totals(cart)
        print_header("RINGKASAN ORDER")
        print(f"Nama pelanggan: {customer_name}")
        rows = [
            [index, name, item[0], format_rupiah(item[1])]
            for index, (name, item) in enumerate(cart.items(), start=1)
        ]
        print_table("ITEM DIPESAN", ["No", "Menu", "Qty", "Subtotal"], rows, [4, 30, 6, 14], align_right={0, 2, 3})
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
            options = [
                ("1", "Pilih Menu"),
                ("2", "Search Menu"),
                ("3", "Sorting Menu"),
                ("4", "Lihat Keranjang"),
                ("5", "Checkout"),
                ("0", "Batal Order"),
            ]
            print_menu_options("AKSI ORDER", options)

            try:
                choice = prompt_menu_choice("Pilih: ", options)
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
                    show_suggestion(keyword, self.menu_manager.menu.keys(), "Menu")
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
            menu_index = prompt_number("Nomor menu: ", min_value=1, max_value=len(active_items))
            qty = prompt_number("Quantity: ", min_value=1)
        except (ValueError, EOFError, KeyboardInterrupt):
            print("Input tidak valid")
            return

        name, price = active_items[menu_index - 1]
        subtotal = price * qty
        if name in cart:
            old_qty, old_subtotal = cart[name]
            cart[name] = [old_qty + qty, old_subtotal + subtotal]
            print(color_text(f"{name} sudah ada di keranjang. Quantity digabung menjadi {cart[name][0]}.", "cyan", "bold"))
        else:
            cart[name] = [qty, subtotal]
            print(f"{name} x{qty} masuk keranjang")

    def checkout_customer_order(self, customer_name, cart):
        if not cart:
            print("Keranjang masih kosong")
            return False

        subtotal, tax, grand_total = self.show_order_summary(customer_name, cart)

        try:
            confirm = prompt_confirm("Konfirmasi checkout? (y/n): ")
        except (EOFError, KeyboardInterrupt):
            return False

        if confirm:
            order_no = self.order_manager.place_order(customer_name, cart, subtotal, tax, grand_total)
            print("Order berhasil dibuat.")
            print(f"Nomor order kamu: {order_no}")
            print("Silakan bayar di kasir.")
            wait_enter()
            return True

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
