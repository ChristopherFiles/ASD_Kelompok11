import json
import datetime
import re
import sys
import os
import qrcode
import barcode
import matplotlib.pyplot as plt

from barcode.writer import ImageWriter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import pagesizes
from reportlab.lib.units import inch

MENU_FILE = "menu.json"
SALES_FILE = "sales.json"
LOGO_PATH = "logo_cafe.png"

USERS = {
    "admin": "1234",
    "kasir": "1234"
}

# ================= UTILITIES =================

def safe_input(prompt):
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print("\n↩ Kembali ke Menu Utama...")
        raise

def format_rupiah(n):
    return f"Rp{int(n):,}".replace(",", ".")

def parse_number(text):
    clean = re.sub(r"[^\d]", "", text)
    if clean == "":
        raise ValueError
    return int(clean)

# ================= MENU MANAGER =================

class MenuManager:
    def __init__(self):
        self.menu = self.load()

    def load(self):
        try:
            with open(MENU_FILE, "r") as f:
                menu = json.load(f)
                if isinstance(menu, dict):
                    return menu
                return {}
        except:
            return {}

    def save(self):
        with open(MENU_FILE, "w") as f:
            json.dump(self.menu, f, indent=4)

    def show(self, menu_data=None):
        menu_data = self.menu if menu_data is None else menu_data
        print("\n📋 DAFTAR MENU")
        print("="*52)
        if not menu_data:
            print("Belum ada menu")
        else:
            for index, (name, price) in enumerate(menu_data.items(), start=1):
                print(f"{index:>2}. {name:<28} {format_rupiah(price):>15}")
        print("="*52)

    def add(self):
        try:
            name = safe_input("Nama menu: ").title()
            price = parse_number(safe_input("Harga: "))
            self.menu[name] = price
            self.save()
            print("✔ Menu ditambahkan")
        except:
            print("❌ Input tidak valid")

    def update(self):
        try:
            name = safe_input("Nama menu: ").title()
            if name not in self.menu:
                print("Menu tidak ada")
                return
            price = parse_number(safe_input("Harga baru: "))
            self.menu[name] = price
            self.save()
            print("✔ Menu diperbarui")
        except:
            print("❌ Input tidak valid")

    def delete(self):
        try:
            name = safe_input("Nama menu: ").title()
            if name in self.menu:
                del self.menu[name]
                self.save()
                print("✔ Menu dihapus")
        except:
            print("❌ Input tidak valid")

    def search(self):
        keyword = safe_input("Cari menu berdasarkan nama/harga: ").strip().lower()
        if not keyword:
            print("Kata kunci tidak boleh kosong")
            return

        digits = re.sub(r"[^\d]", "", keyword)
        result = {
            name: price
            for name, price in self.menu.items()
            if keyword in name.lower() or (digits and digits in str(price))
        }

        if not result:
            print("Menu tidak ditemukan")
            return

        print(f"\nHasil pencarian untuk '{keyword}':")
        self.show(result)

    def sort_menu(self):
        print("\n--- SORTING MENU ---")
        print("1. Nama A-Z")
        print("2. Nama Z-A")
        print("3. Harga Termurah")
        print("4. Harga Termahal")

        choice = safe_input("Pilih: ")
        if choice == "1":
            sorted_items = sorted(self.menu.items(), key=lambda item: item[0].lower())
        elif choice == "2":
            sorted_items = sorted(self.menu.items(), key=lambda item: item[0].lower(), reverse=True)
        elif choice == "3":
            sorted_items = sorted(self.menu.items(), key=lambda item: (item[1], item[0].lower()))
        elif choice == "4":
            sorted_items = sorted(self.menu.items(), key=lambda item: (item[1], item[0].lower()), reverse=True)
        else:
            print("Pilihan tidak valid")
            return

        self.show(dict(sorted_items))

# ================= PDF GENERATOR =================

class PDFGenerator:

    def generate_invoice(self, invoice_no, cart, total, discount, tax, grand_total):
        filename = f"Invoice_{invoice_no}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=pagesizes.A4)
        elements = []
        styles = getSampleStyleSheet()

        try:
            elements.append(Image(LOGO_PATH, width=1.5*inch, height=1.5*inch))
        except:
            pass

        elements.append(Paragraph("<b>CAFE ENTERPRISE</b>", styles['Title']))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"Invoice: {invoice_no}", styles['Normal']))
        elements.append(Paragraph(f"Tanggal: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 15))

        data = [["Menu", "Qty", "Subtotal"]]

        for name, qty in cart.items():
            data.append([name, qty[0], format_rupiah(qty[1])])

        data.append(["", "", ""])
        data.append(["Total", "", format_rupiah(total)])
        data.append(["Diskon", "", f"{discount}%"])
        data.append(["Pajak 10%", "", format_rupiah(tax)])
        data.append(["Grand Total", "", format_rupiah(grand_total)])

        table = Table(data, colWidths=[200, 50, 150])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
            ('TEXTCOLOR',(0,0),(-1,0),colors.white),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('ALIGN',(1,1),(-1,-1),'CENTER')
        ]))

        elements.append(table)
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Terima kasih ☕", styles['Normal']))

        doc.build(elements)
        os.startfile(filename)

    def generate_receipt(self, invoice_no, cart, grand_total):
        filename = f"Struk_{invoice_no}.pdf"
        width = 226
        height = 800