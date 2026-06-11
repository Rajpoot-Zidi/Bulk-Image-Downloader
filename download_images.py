import os
import re
import requests
from urllib.parse import urlparse
from io import BytesIO

# Optional OCR
try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False

# rembg/background removal removed per user request
REMBG_AVAILABLE = False

URL_FILE = "image_urls.txt"
OUTPUT_DIR = "downloaded_images"
REJECTED_DIR = os.path.join(OUTPUT_DIR, "rejected")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(REJECTED_DIR, exist_ok=True)


def extract_product_code_from_url(url):
    filename = os.path.basename(urlparse(url).path)

    patterns = [
        r'va\d{4,10}',   # VA18313
        r'k\d{5,10}',    # k220750
        r'v\d{5,10}',    # v12345
        r'ed\d{5,10}',   # ed12345 (NEW)
    ]

    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            return match.group(0).lower()

    return None


def get_extension_from_url(url):
    path = urlparse(url).path
    ext = os.path.splitext(path)[1]
    return ext if ext else ".jpg"


def normalize_code(s: str) -> str:
    if not s:
        return ""
    return re.sub(r'[^a-z0-9]', '', s.lower())


def sanitize_filename(s: str) -> str:
    """Make a safe filename from the provided SKU/label.

    Keeps letters, numbers, dot, underscore and hyphen. Replaces other chars with underscore.
    Truncates to a reasonable length and ensures a non-empty name.
    """
    if not s:
        return "image"
    name = s.strip()
    # remove path parts in case someone supplied a path
    name = os.path.basename(name)
    # Replace disallowed chars
    name = re.sub(r'[^A-Za-z0-9._-]', '_', name)
    # Prevent very long filenames
    return name[:200] if name else "image"


def parse_line(line: str):
    """
    Accepts lines in any of the following forms (whitespace or comma separated):
      - url
      - url sku_or_expected_code
      - url,sku_or_expected_code
    Returns (url, sku_or_None)
    """
    s = line.strip()
    if not s or s.startswith('#'):
        return None, None

    # CSV style first
    if ',' in s:
        parts = [p.strip() for p in s.split(',', 1)]
        if len(parts) == 2:
            return parts[0], parts[1]

    # whitespace separated
    parts = s.split()
    if len(parts) == 1:
        return parts[0], None
    else:
        return parts[0], parts[1]


def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Download images and optionally verify SKUs via OCR")
    parser.add_argument('input', nargs='?', default=URL_FILE, help='Input file with URLs (default: image_urls.txt)')
    parser.add_argument('--force', '-f', action='store_true', help='Re-download/process even if target file exists')
    return parser.parse_args()


args = parse_args()

with open(args.input, "r", encoding="utf-8") as f:
    lines = [line.rstrip('\n') for line in f]

for line in lines:
    url, expected_code = parse_line(line)
    if not url:
        continue

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Determine SKU/name to save: prefer provided expected_code (treated as desired filename),
        # fall back to extraction from URL or the URL's basename.
        sku = expected_code if expected_code else extract_product_code_from_url(url)

        if not sku:
            print(f"⚠ No SKU provided or found in URL: {url}")
            sku = os.path.splitext(os.path.basename(urlparse(url).path))[0]

        safe_name = sanitize_filename(sku)
        ext = get_extension_from_url(url)
        filepath = os.path.join(OUTPUT_DIR, f"{safe_name}{ext}")

        # skip duplicates unless forced
        if os.path.exists(filepath) and not args.force:
            print(f"⏩ Skipped (already exists): {os.path.basename(filepath)}")
            continue

        content = response.content

        # No background removal: use original content
        processed_content = content
        used_png = False

        # If OCR is available and an expected code was provided, verify it appears on the image
        if OCR_AVAILABLE and expected_code:
            try:
                img = Image.open(BytesIO(processed_content))
                ocr_text = pytesseract.image_to_string(img)
                norm_ocr = normalize_code(ocr_text)
                norm_expected = normalize_code(expected_code)

                if norm_expected and norm_expected in norm_ocr:
                    with open(filepath, "wb") as f:
                        f.write(processed_content)
                    print(f"✓ Saved & Verified: {os.path.basename(filepath)}")
                else:
                    # Save to rejected folder for manual review
                    rejected_path = os.path.join(REJECTED_DIR, f"{safe_name}_REJECTED{ext}")
                    with open(rejected_path, "wb") as f:
                        f.write(processed_content)
                    print(f"✗ Verification failed (code not found on image): {safe_name} — saved to rejected/")

            except pytesseract.TesseractNotFoundError:
                # Tesseract binary not installed; fall back to saving without verification
                with open(filepath, "wb") as f:
                    f.write(processed_content)
                print(f"⚠ Tesseract not found. Saved without verification: {os.path.basename(filepath)}")
            except Exception as e:
                # Any other OCR error: save and report
                with open(filepath, "wb") as f:
                    f.write(processed_content)
                print(f"⚠ OCR error, saved without verification: {os.path.basename(filepath)} → {e}")

        else:
            # OCR not available or no expected code: save file normally
            with open(filepath, "wb") as f:
                f.write(processed_content)
            if expected_code and not OCR_AVAILABLE:
                print(f"⚠ OCR not available; saved without verification: {os.path.basename(filepath)}")
            else:
                print(f"✓ Saved: {os.path.basename(filepath)}")

    except Exception as e:
        print(f"✗ Failed: {url} → {e}")

print("\nDONE 🚀 Clean download complete.")