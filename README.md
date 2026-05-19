# Cafe Enterprise System

Sistem manajemen cafe berbasis Python untuk admin, kasir, dan pelanggan. Versi ini memakai tampilan terminal biru, efek typing ala terminal hacker, pengelolaan menu, order pelanggan, pembayaran kasir, laporan PDF, dan dashboard penjualan.

## Fitur Utama

### Tampilan Terminal
- Tema teks biru/cyan dengan ANSI color.
- Banner startup dengan animasi typing.
- Menu, tabel, ringkasan order, dan status dibuat lebih rapi.
- Mode cepat tersedia dengan environment variable `CAFE_FAST=1`.

### Admin
- Lihat menu.
- Cari dan sorting menu.
- Reset tampilan hasil pencarian.
- Tambah, update, dan hapus menu.
- Laporan bulanan PDF.
- Dashboard grafik menu terlaris.
- Dashboard bisnis ringkas: total transaksi, pendapatan, rata-rata transaksi, item terjual, order pending, dan top menu.

### Kasir
- Konfirmasi pembayaran order.
- Validasi nominal bayar dan hitung kembalian.
- Cek status order.
- Cetak invoice A4 atau struk thermal PDF.
- Akses laporan bulanan, grafik, dan dashboard bisnis.

### Pelanggan
- Buat order dengan nama pelanggan.
- Cari dan sorting menu.
- Reset daftar menu setelah pencarian.
- Lihat keranjang.
- Ubah quantity item keranjang.
- Hapus item dari keranjang.
- Checkout dan mendapatkan nomor order.
- Cek status order.
- Rekomendasi menu berdasarkan tren penjualan dan budget.

## Struktur File

```text
ASD_Kelompok11-main/
  cafe.py
  cafe.py.bak
  menu.json
  orders.json
  sales.json
  README.md
```

## Kebutuhan Opsional

Program inti bisa berjalan tanpa library tambahan. Beberapa fitur membutuhkan package berikut:

```bash
pip install reportlab matplotlib pillow
```

- `reportlab` dipakai untuk invoice, struk, dan laporan PDF.
- `matplotlib` dipakai untuk dashboard grafik.
- `pillow` biasanya dibutuhkan oleh ReportLab ketika memproses gambar/logo.

## Cara Menjalankan

Masuk ke folder proyek, lalu jalankan:

```bash
python cafe.py
```

Jika ingin mematikan animasi typing supaya program lebih cepat:

```bash
set CAFE_FAST=1
python cafe.py
```

Di PowerShell:

```powershell
$env:CAFE_FAST="1"
python cafe.py
```

## Login Default

| Role | Username | Password |
| --- | --- | --- |
| Admin | `admin` | `1234` |
| Kasir | `kasir` | `1234` |

## Alur Pelanggan

1. Pilih menu `Pelanggan`.
2. Pilih `Order`.
3. Masukkan nama pelanggan.
4. Pilih menu, cari menu, sorting, atau lihat rekomendasi.
5. Cek keranjang dan ubah quantity bila perlu.
6. Checkout untuk mendapatkan nomor order.
7. Bayar ke kasir dengan nomor order tersebut.

## Alur Kasir

1. Pilih menu `Karyawan`.
2. Login sebagai `kasir`.
3. Pilih `Konfirmasi Pembayaran Order`.
4. Pilih order pending.
5. Masukkan nominal bayar.
6. Cetak invoice atau struk jika diperlukan.

## Output File

File output dibuat di folder yang sama dengan `cafe.py`:

```text
Invoice_INV0001.pdf
Struk_INV0001.pdf
Laporan_Bulanan.pdf
```

## Data

- `menu.json` menyimpan daftar menu dan harga.
- `orders.json` menyimpan order pelanggan dan status pembayaran.
- `sales.json` menyimpan transaksi yang sudah dibayar.

Status order:

- `WAITING_PAYMENT`: order sudah dibuat, belum dibayar.
- `PAID`: pembayaran sudah dikonfirmasi kasir.
- `CANCELLED`: order dibatalkan.

## Catatan

Tekan `CTRL+C` atau `CTRL+Z` pada input untuk kembali atau keluar dari menu aktif. Jika warna ANSI tidak tampil benar di terminal lama, jalankan program di Windows Terminal, PowerShell terbaru, atau terminal modern lainnya.
