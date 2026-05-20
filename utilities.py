import datetime
import difflib
import json
import os
import re
import sys
import time


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


def get_sales_item_counts(sales_file):
    sales = load_json_file(sales_file, {})
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


def get_top_menu_items(sales_file, limit=5):
    counts = get_sales_item_counts(sales_file)
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
