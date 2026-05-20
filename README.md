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


---

# BAGIAN 1: FITUR ADMIN (BACK-OFFICE & MANAGEMENT)

Fitur Admin berfokus pada manajemen data menu (*CRUD*) serta pemantauan performa bisnis melalui laporan dan grafik.

### [1] Lihat Menu

* **Struktur Data:** `List` berisi `Tuple` atau `List` baris data `[No, Menu, Harga, Terjual, Status]`.
* **Algoritma & Logika:** Sistem mengambil data menu dari memori, lalu melakukan perulangan (*looping*). Di dalam loop, sistem mencocokkan setiap nama menu dengan data penjualan di `sales.json` melalui fungsi `get_top_menu_items()`. Menu yang menempati peringkat pertama penjualan diberi badge `"PALING LARIS"`, sedangkan peringkat 2-5 diberi badge `"TOP X"`. Data kemudian diformat menjadi tabel menggunakan fungsi `print_table()`.
* **Alasan Pemilihan Struktur Data:** `List` digunakan karena data bersifat dinamis (bisa bertambah/berkurang) dan urutannya harus konsisten dari nomor 1 hingga akhir agar rapi saat dipresentasikan dalam bentuk tabel teks.

### [2] Tambah Menu

* **Struktur Data:** `Dictionary` (`self.menu`).
* **Algoritma & Logika:**
Admin memasukkan nama menu baru. Sistem mengubah teks tersebut menjadi format *Title Case* (huruf besar di awal kata). Sistem melakukan pengecekan instan: `if name in self.menu`. Jika menu sudah ada, proses ditolak. Jika ada kemiripan nama dengan menu lama, algoritma *Fuzzy String Matching* (`difflib`) akan memberikan saran. Jika admin mengonfirmasi, harga divalidasi sebagai angka positif ($>0$), lalu disimpan ke `menu.json`.
* **Alasan Pemilihan Struktur Data:** Pengecekan duplikasi menggunakan operator `in` pada `Dictionary` berjalan dalam waktu konstan $O(1)$, sehingga validasi menu ganda tidak membebani sistem meskipun menu berjumlah ratusan.

### [3] Update Menu

* **Struktur Data:** `Dictionary` (`self.menu`) dan `List` (untuk pencarian *exact lookup*).
* **Algoritma & Logika:**
Sistem meminta nama menu yang ingin diubah. Algoritma pencarian berbasis *exact lookup* (`exact_lookup = {name.lower(): name for name in choices}`) memastikan bahwa meskipun admin menulis dengan huruf kecil semua, sistem tetap dapat menemukannya. Setelah menu ditemukan, nilai harga (*value*) di dalam dictionary langsung diperbarui berdasarkan input harga baru, lalu memicu fungsi `self.save()` untuk memperbarui berkas JSON.
* **Alasan Pemilihan Struktur Data:** Memperbarui data pada `Dictionary` sangat efisien karena kita hanya perlu menembak kata kuncinya secara langsung: `self.menu[name] = price` tanpa perlu mencari posisinya satu per satu.

### [4] Hapus Menu

* **Struktur Data:** `Dictionary` (`self.menu`).
* **Algoritma & Logika:**
Sistem menampilkan seluruh menu terlebih dahulu. Admin memasukkan nama menu yang ingin dihapus. Melalui fungsi `prompt_existing_name()`, nama menu divalidasi. Jika valid, sistem memicu perintah konfirmasi (`prompt_confirm`). Jika disetujui, fungsi bawaan Python `del self.menu[name]` dieksekusi, dan status menu langsung sinkron dengan berkas penyimpanan.
* **Alasan Pemilihan Struktur Data:** Operasi penghapusan elemen `del` pada `Dictionary` berbasis *hash table* memiliki kompleksitas waktu $O(1)$, menjadikannya pilihan terbaik untuk eksekusi instan.

### [5] Laporan Bulanan

* **Struktur Data:** `List` berisi `Tuple` data penjualan, `Dictionary` (`item_count`) untuk agregasi produk.
* **Algoritma & Logika:**
Sistem membaca `sales.json`, lalu mengurutkannya berdasarkan tanggal terbaru menggunakan algoritma **Timsort** (`sorted()`). Sistem melakukan akumulasi total pendapatan dengan fungsi `sum()`, menghitung rata-rata dengan pembagian matematika standar, dan melakukan agregasi kuantitas item terjual ke dalam `item_count`. Data tersebut kemudian dipetakan ke dalam komponen tabel ReportLab untuk diwujudkan menjadi dokumen **PDF Resmi A4**.
* **Alasan Pemilihan Struktur Data:** `Dictionary` digunakan untuk akumulasi (`item_count.get(item_name, 0) + qty`) karena mampu mengelompokkan total terjual per produk secara adaptif tanpa perlu membuat struktur data kaku sejak awal.

### [6] Dashboard Grafik

* **Struktur Data:** `Dictionary` (`item_count`).
* **Algoritma & Logika:**
Sistem melakukan ekstraksi data penjualan dari `sales.json`. Nama produk dijadikan sebagai *Keys* (Sumbu X) dan akumulasi kuantitas terjual dijadikan sebagai *Values* (Sumbu Y). Algoritma kemudian meneruskan data ini ke library `matplotlib.pyplot` untuk merender **Grafik Batang (Bar Chart)**.
* **Alasan Pemilihan Struktur Data:** Pasangan *Key-Value* pada dictionary sangat selaras dengan kebutuhan visualisasi data Sumbu X (Label) dan Sumbu Y (Nilai) pada pembuatan grafik.

### [7] Riwayat Transaksi

* **Struktur Data:** `List` multidimensi untuk baris tabel.
* **Algoritma & Logika:**
Sistem memuat data penjualan dan data order. Melalui perulangan, sistem mengekstrak detail waktu nyata (Hari, Tanggal, Jam) menggunakan fungsi helper `format_realtime_history()`. Jika ada data order yang kosong, sistem menjalankan algoritma pencarian silang (*cross-reference loop*) untuk mencocokkan `invoice_no` pada penjualan dengan data di antrean order agar nama pelanggan tetap muncul.
* **Alasan Pemilihan Struktur Data:** `List` multidimensi dipilih karena format ini merupakan standar input yang dibutuhkan oleh fungsi `print_table()` untuk melakukan iterasi baris dan kolom secara presisi.

---

# BAGIAN 2: FITUR KASIR (FRONT-OFFICE & TRANSACTION)

Fitur Kasir berfokus pada eksekusi pembayaran, validasi antrean, dan pemantauan data finansial harian.

```
[Antrean Order] ---> [Kasir Validasi Pembayaran] ---> [Hitung Kembalian] ---> [Cetak Struk/PDF]

```

### [1] Konfirmasi Pembayaran Order

* **Struktur Data:** `List` berisi `Tuple` `(order_no, order_data)`.
* **Algoritma & Logika:**
Sistem memfilter order yang memiliki status `WAITING_PAYMENT`. Kasir memilih nomor urut order. Sistem menampilkan detail pesanan dan total yang harus dibayar. Kasir memasukkan nominal uang tunai.
* **Logika Kondisional:** Jika `Uang < Grand Total`, sistem menolak transaksi. Jika `Uang >= Grand Total`, sistem menghitung `Kembalian = Uang - Grand Total`.
Sistem menghasilkan nomor invoice baru (`INVXXXX`), mengubah status menjadi `PAID`, memindahkan data ke `sales.json`, serta menawarkan opsi cetak PDF (Invoice A4 / Struk Thermal).


* **Alasan Pemilihan Struktur Data:** Hasil filter order berupa `List` bertipe `Tuple` digunakan agar kasir bisa memilih order hanya dengan mengetik angka indeksnya (`1`, `2`, `3`) secara praktis di terminal.

### [2] Cek Status Order

* **Struktur Data:** `List` dari data order yang telah diurutkan.
* **Algoritma & Logika:**
Sistem menampilkan seluruh order (baik `WAITING_PAYMENT` maupun `PAID`) diurutkan dari yang paling baru menggunakan parameter `parse_datetime`. Kasir dapat memilih opsi "Lihat Detail Order" dan memasukkan kode order (misal: `ORD0001`). Sistem akan mencari data tersebut di database order dan menampilkan rincian item beserta status pembayaran spesifik untuk kasir.
* **Alasan Pemilihan Struktur Data:** `List` digunakan untuk menampung hasil pengurutan data teranyar sebelum disajikan ke hadapan kasir.

### [3] Laporan Bulanan, [4] Dashboard Grafik, & [5] Riwayat Transaksi (Fitur Kasir)

* **Struktur Data & Logika:** Sama dengan fitur Admin (Menu [5], [6], [7]).
* **Penjelasan Presentasi:** Fitur ini sengaja disediakan juga di menu Kasir agar kasir memiliki akses langsung (*read-only*) terhadap performa penjualan dan riwayat transaksi tanpa harus berpindah ke akun Admin, sehingga mempercepat proses *clerical* di meja kasir.

---

# BAGIAN 3: FITUR CUSTOMER (ORDERING SYSTEM)

Fitur Customer dirancang dengan pendekatan *User Experience* (UX) yang aman, interaktif, dan mudah digunakan oleh pelanggan mandiri.

### [1] Order

* **Struktur Data:** `String` untuk nama pelanggan, `Dictionary` untuk keranjang belanja (`cart`).
* **Algoritma & Logika:**
Pelanggan menginput nama sebagai identitas utama order. Sistem kemudian membuka sub-menu transaksi. Di dalam sub-menu ini, pelanggan dapat mengisi keranjang belanja, mencari menu, mengurutkannya, hingga melakukan checkout.
* **Alasan Pemilihan Struktur Data:** `Dictionary` digunakan sebagai basis objek `cart` agar penambahan item yang sama berulang kali tidak membuat baris baru, melainkan diakumulasikan.

### [2] Cek Status Order (Menu Utama Customer)

* **Struktur Data:** `Dictionary` (`self.orders`).
* **Algoritma & Logika:**
Pelanggan memasukkan kode order mereka (Contoh: `ORD0002`). Sistem mencari kode tersebut. Jika pelanggan salah ketik, fungsi `suggest_order_no()` dengan algoritma kemiripan teks akan memprediksi kode yang dimaksud. Jika ditemukan, sistem menampilkan detail item dan memberikan pesan edukatif: *"Silakan bayar di kasir"* (jika `WAITING_PAYMENT`) atau *"Pembayaran sudah dikonfirmasi"* (jika `PAID`).
* **Alasan Pemilihan Struktur Data:** Pencarian kode order pada `Dictionary` menggunakan metode `.get()` memastikan pencarian kilat $O(1)$ sehingga pelanggan tidak perlu menunggu lama.

---

## SUB-MENU DI DALAM FITUR ORDER CUSTOMER:

### [1] Pilih Menu

* **Struktur Data:** `Dictionary` `cart = {"Nama Menu": [Qty, Subtotal]}`.
* **Algoritma & Logika:**
Pelanggan memilih nomor menu dari daftar aktif dan memasukkan kuantitas (`qty`). Sistem mengambil data nama dan harga menu.
* **Logika Akumulasi:** Sistem mengecek `if name in cart:`. Jika TRUE, kuantitas lama ditambahkan kuantitas baru, dan subtotal diperbarui (`harga * qty`). Jika FALSE, item baru dimasukkan ke keranjang.


* **Alasan Pemilihan Struktur Data:** Format Array `[Qty, Subtotal]` di dalam value `Dictionary` dipilih untuk mempermudah pemisahan data kuantitas dan finansial saat perhitungan nota.

### [2] Search Menu

* **Struktur Data:** `Dictionary` (Hasil filter pencarian).
* **Algoritma & Logika:**
Pelanggan memasukkan kata kunci (nama atau harga). Sistem melakukan pembersihan karakter non-digit untuk pencarian harga menggunakan Regex `re.sub()`. Sistem kemudian melakukan penyaringan menggunakan *Dictionary Comprehension*:
`{name: price for name, price in self.menu.items() if keyword in name.lower() or (digits and digits in str(price))}`
Hasilnya akan langsung ditampilkan dalam bentuk tabel pencarian yang spesifik.
* **Alasan Pemilihan Struktur Data:** *Dictionary Comprehension* menghasilkan dictionary baru secara instan di memori, menjaga efisiensi penggunaan RAM.

### [3] Sorting Menu

* **Struktur Data:** `List` berisi `Tuple` pasangan `(Nama Menu, Harga)`.
* **Algoritma & Logika:**
Pelanggan memilih 1 dari 4 opsi pengurutan (Harga Naik, Harga Turun, A-Z, Z-A). Sistem menggunakan fungsi bawaan `sorted()` dengan parameter `key=lambda item: item[1]` (untuk harga) atau `item[0]` (untuk nama). Argumen `reverse=True` diaktifkan jika pelanggan memilih opsi menurun (*descending*).
* **Alasan Pemilihan Struktur Data:** Data dictionary menu diubah menjadi `List` of `Tuple` terlebih dahulu karena dictionary murni di Python tidak didesain untuk diurutkan berdasarkan nilainya secara langsung. `List` menjamin urutan elemen hasil sorting tetap konsisten saat ditampilkan.

### [4] Lihat Keranjang

* **Struktur Data:** `List` multidimensi untuk pembuatan baris tabel.
* **Algoritma & Logika:**
Sistem membaca isi `cart`. Jika kosong, muncul pesan peringatan. Jika berisi item, sistem melakukan iterasi untuk menyusun data ke dalam tabel terminal. Di akhir tabel, fungsi `calculate_cart_totals()` dipicu untuk menghitung secara *real-time*: `Subtotal`, `Pajak = Subtotal * 0.10`, dan `Grand Total = Subtotal + Pajak`.
* **Alasan Pemilihan Struktur Data:** Perhitungan total langsung menggunakan fungsi matematika dasar pada nilai numerik yang diekstrak dari elemen *list* di dalam *dictionary* keranjang.

### [5] Checkout

* **Struktur Data:** `Dictionary` JSON untuk objek order baru.
* **Algoritma & Logika:**
Sistem menampilkan ringkasan akhir seluruh pesanan kepada pelanggan. Setelah mendapatkan konfirmasi `Ya`, fungsi `place_order()` di dalam `OrderManager` akan aktif. Fungsi ini menghasilkan ID unik kontinu (Contoh: `ORD0005`) dengan algoritma penomoran otomatis, menyisipkan waktu saat ini (`now_string()`), menyetel status menjadi `WAITING_PAYMENT`, lalu menulis data tersebut secara permanen ke file `orders.json`. Keranjang belanja pelanggan kemudian dikosongkan untuk transaksi berikutnya.
* **Alasan Pemilihan Struktur Data:** Penyusunan objek order dalam bentuk bertingkat (*nested dictionary*) di Python mempermudah konversi data menjadi format teks terstruktur di dalam berkas JSON.

kita pake linear search karna menu dan queuenya sedikit