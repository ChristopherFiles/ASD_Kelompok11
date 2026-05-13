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
    from reportlab.lib import pagesizes
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
except ImportError:
    colors = None
    pagesizes = None
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
LOGO_PATH = os.path.join(BASE_DIR, "logo_cafe.png")

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

        if isinstance(menu_data, dict):
            items = list(menu_data.items())
        else:
            items = list(menu_data)

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

            price = parse_number(safe_input("Harga: "))
            self.menu[name] = price
            self.save()
            print("Menu ditambahkan")
        except:
            print("Input tidak valid")

    def update(self):
        try:
            name = safe_input("Nama menu: ").strip().title()
            if name not in self.menu:
                print("Menu tidak ada")
                return

            price = parse_number(safe_input("Harga baru: "))
            self.menu[name] = price
            self.save()
            print("Menu diperbarui")
        except:
            print("Input tidak valid")

    def delete(self):
        try:
            name = safe_input("Nama menu: ").strip().title()
            if name in self.menu:
                del self.menu[name]
                self.save()
                print("Menu dihapus")
            else:
                print("Menu tidak ada")
        except:
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
        except:
            print("Kembali...")
            return {}

    def get_sorted_items(self, choice):
        if choice == "1":
            return sorted(self.menu.items(), key=lambda item: item[0].lower())
        if choice == "2":
            return sorted(self.menu.items(), key=lambda item: item[0].lower(), reverse=True)
        if choice == "3":
            return sorted(self.menu.items(), key=lambda item: (item[1], item[0].lower()))
        if choice == "4":
            return sorted(self.menu.items(), key=lambda item: (item[1], item[0].lower()), reverse=True)
        return None

    def sort_menu(self):
        try:
            print("\n--- SORTING MENU ---")
            print("1. Nama A-Z")
            print("2. Nama Z-A")
            print("3. Harga Termurah")
            print("4. Harga Termahal")

            choice = safe_input("Pilih: ").strip()
            sorted_items = self.get_sorted_items(choice)

            if sorted_items is None:
                print("Pilihan tidak valid")
                return []

            self.show(sorted_items, "HASIL SORTING")
            return sorted_items
        except:
            print("Kembali...")
            return []

    def pick_for_transaction(self):
        view_items = list(self.menu.items())

        while True:
            self.show(view_items)
            print("Ketik nomor menu untuk memilih")
            print("S = Search, O = Sorting, X = Selesai")
            choice = safe_input("Pilih menu: ").strip().lower()

            if choice == "x":
                return None
            if choice == "s":
                result = self.search()
                if result:
                    view_items = list(result.items())
                continue
            if choice == "o":
                sorted_items = self.sort_menu()
                if sorted_items:
                    view_items = sorted_items
                continue

            try:
                index = int(choice)
                if 1 <= index <= len(view_items):
                    return view_items[index - 1]
                print("Nomor menu tidak ada")
            except ValueError:
                print("Pilihan tidak valid")


# ================= PDF GENERATOR =================

class PDFGenerator:
    def is_available(self):
        return SimpleDocTemplate is not None

    def open_file(self, filename):
        try:
            os.startfile(filename)
        except OSError:
            print(f"File berhasil dibuat: {filename}")

    def generate_invoice(self, invoice_no, cart, total, discount, tax, grand_total):
        if not self.is_available():
            print("ReportLab belum terinstall. Tidak bisa membuat PDF invoice.")
            return

        filename = os.path.join(BASE_DIR, f"Invoice_{invoice_no}.pdf")
        doc = SimpleDocTemplate(filename, pagesize=pagesizes.A4)
        elements = []
        styles = getSampleStyleSheet()

        try:
            elements.append(Image(LOGO_PATH, width=1.5 * inch, height=1.5 * inch))
        except:
            pass

        elements.append(Paragraph("<b>CAFE ENTERPRISE</b>", styles["Title"]))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"Invoice: {invoice_no}", styles["Normal"]))
        elements.append(Paragraph(f"Tanggal: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M')}", styles["Normal"]))
        elements.append(Spacer(1, 15))

        data = [["Menu", "Qty", "Subtotal"]]

        for name, item in cart.items():
            data.append([name, item[0], format_rupiah(item[1])])

        data.append(["", "", ""])
        data.append(["Total", "", format_rupiah(total)])
        data.append(["Diskon", "", f"{discount}%"])
        data.append(["Pajak 10%", "", format_rupiah(tax)])
        data.append(["Grand Total", "", format_rupiah(grand_total)])

        table = Table(data, colWidths=[200, 50, 150])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Terima kasih", styles["Normal"]))

        doc.build(elements)
        self.open_file(filename)

    def generate_receipt(self, invoice_no, cart, grand_total):
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
        styles = getSampleStyleSheet()
        elements = [
            Paragraph("<b>CAFE ENTERPRISE</b>", styles["Title"]),
            Paragraph(f"Invoice: {invoice_no}", styles["Normal"]),
            Paragraph(datetime.datetime.now().strftime("%d-%m-%Y %H:%M"), styles["Normal"]),
            Spacer(1, 10),
        ]

        data = [["Item", "Qty", "Subtotal"]]
        for name, item in cart.items():
            data.append([name, item[0], format_rupiah(item[1])])
        data.append(["TOTAL", "", format_rupiah(grand_total)])

        table = Table(data, colWidths=[100, 35, 65])
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("Terima kasih", styles["Normal"]))

        doc.build(elements)
        self.open_file(filename)


# ================= TRANSACTION =================

class TransactionManager:
    def __init__(self, menu_manager):
        self.menu_manager = menu_manager
        self.sales = self.load()
        self.invoice_counter = len(self.sales) + 1
        self.pdf = PDFGenerator()

    def load(self):
        data = load_json_file(SALES_FILE, {})
        return data if isinstance(data, dict) else {}

    def save(self):
        save_json_file(SALES_FILE, self.sales)

    def kasir_menu(self):
        while True:
            print("\n--- MENU KASIR ---")
            print("1. Transaksi")
            print("2. Search Menu")
            print("3. Sorting Menu")
            print("4. Laporan Bulanan")
            print("5. Dashboard Grafik")
            print("0. Kembali")

            try:
                choice = safe_input("Pilih: ").strip()

                if choice == "1":
                    self.transact()
                elif choice == "2":
                    self.menu_manager.search()
                    wait_enter()
                elif choice == "3":
                    self.menu_manager.sort_menu()
                    wait_enter()
                elif choice == "4":
                    self.generate_monthly_report()
                elif choice == "5":
                    self.show_chart()
                elif choice == "0":
                    break
                else:
                    print("Pilihan tidak valid")
            except:
                break

    def transact(self):
        try:
            cart = {}
            total = 0

            while True:
                selected = self.menu_manager.pick_for_transaction()
                if selected is None:
                    break

                name, price = selected
                qty = parse_number(safe_input("Jumlah: "))
                if qty <= 0:
                    print("Jumlah harus lebih dari 0")
                    continue

                subtotal = price * qty
                if name in cart:
                    old_qty, old_subtotal = cart[name]
                    cart[name] = (old_qty + qty, old_subtotal + subtotal)
                else:
                    cart[name] = (qty, subtotal)

                total += subtotal
                print(f"{name} x{qty} masuk keranjang")

            if not cart:
                return

            discount_text = safe_input("Diskon (%) [enter jika 0]: ").strip()
            discount = float(discount_text) if discount_text else 0
            total_after_discount = total - (total * discount / 100)
            tax = total_after_discount * 0.10
            grand_total = round(total_after_discount + tax)

            print("\n--- RINGKASAN TRANSAKSI ---")
            for name, item in cart.items():
                print(f"{name:<30} x{item[0]:<3} {format_rupiah(item[1]):>12}")
            print("-" * 50)
            print(f"Total     : {format_rupiah(total)}")
            print(f"Diskon    : {discount}%")
            print(f"Pajak 10% : {format_rupiah(tax)}")
            print(f"Grand Total: {format_rupiah(grand_total)}")

            pay = parse_number(safe_input("Bayar: "))
            if pay < grand_total:
                print("Uang bayar kurang. Transaksi dibatalkan.")
                return

            print("Kembalian:", format_rupiah(pay - grand_total))

            invoice_no = f"INV{self.invoice_counter:04d}"
            self.invoice_counter += 1

            self.sales[invoice_no] = {
                "tanggal": str(datetime.datetime.now()),
                "items": cart,
                "total": grand_total,
            }

            self.save()

            print("\n1. Invoice A4")
            print("2. Struk Thermal")
            print("0. Tidak cetak")
            cetak = safe_input("Pilih cetak: ").strip()

            if cetak == "1":
                self.pdf.generate_invoice(invoice_no, cart, total, discount, tax, grand_total)
            elif cetak == "2":
                self.pdf.generate_receipt(invoice_no, cart, grand_total)

            print(f"Transaksi {invoice_no} berhasil disimpan")
        except:
            print("Kembali...")

    def generate_monthly_report(self):
        if not self.pdf.is_available():
            print("ReportLab belum terinstall. Tidak bisa membuat laporan PDF.")
            return

        filename = os.path.join(BASE_DIR, "Laporan_Bulanan.pdf")
        doc = SimpleDocTemplate(filename, pagesize=pagesizes.A4)
        elements = []
        styles = getSampleStyleSheet()

        elements.append(Paragraph("<b>LAPORAN BULANAN</b>", styles["Title"]))
        elements.append(Spacer(1, 20))

        total_income = 0
        data = [["Invoice", "Tanggal", "Total"]]

        for inv, sale in self.sales.items():
            total_income += sale["total"]
            data.append([inv, sale["tanggal"][:10], format_rupiah(sale["total"])])

        data.append(["TOTAL", "", format_rupiah(total_income)])

        table = Table(data, colWidths=[100, 150, 150])
        table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 1, colors.black)]))
        elements.append(table)

        doc.build(elements)
        self.pdf.open_file(filename)

    def show_chart(self):
        if plt is None:
            print("Matplotlib belum terinstall. Tidak bisa menampilkan grafik.")
            return

        item_count = {}

        for sale in self.sales.values():
            for item_name, item_data in sale.get("items", {}).items():
                qty = item_data[0] if isinstance(item_data, (list, tuple)) else 1
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
        self.transaction_manager = TransactionManager(self.menu_manager)

    def login(self):
        while True:
            try:
                print("\n=== LOGIN ===")
                user = safe_input("Username: ").strip().lower()
                pw = safe_input("Password: ").strip()
                if user in USERS and USERS[user] == pw:
                    return user
                print("Login salah")
            except:
                sys.exit()

    def run(self):
        while True:
            user = self.login()

            if user == "admin":
                self.admin_menu()
            elif user == "kasir":
                self.transaction_manager.kasir_menu()

    def admin_menu(self):
        while True:
            print("\n--- ADMIN ---")
            print("1. Lihat Menu")
            print("2. Search Menu")
            print("3. Sorting Menu")
            print("4. Tambah Menu")
            print("5. Update Menu")
            print("6. Hapus Menu")
            print("0. Logout")

            try:
                choice = safe_input("Pilih: ").strip()

                if choice == "1":
                    self.menu_manager.show()
                    wait_enter()
                elif choice == "2":
                    self.menu_manager.search()
                    wait_enter()
                elif choice == "3":
                    self.menu_manager.sort_menu()
                    wait_enter()
                elif choice == "4":
                    self.menu_manager.add()
                elif choice == "5":
                    self.menu_manager.update()
                elif choice == "6":
                    self.menu_manager.delete()
                elif choice == "0":
                    break
                else:
                    print("Pilihan tidak valid")
            except:
                break


if __name__ == "__main__":
    CafeSystem().run()
