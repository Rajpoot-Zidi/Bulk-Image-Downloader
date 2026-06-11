<<<<<<< HEAD
# Image Downloader - run by double-click

This project downloads images listed in `image_urls.txt` into the `downloaded_images/` folder using `download_images.py`.

New: each input line can optionally include the expected product code (so the script will verify the code appears on the image using OCR).

Input file formats supported (one entry per line):

- URL only
- URL expected_code (whitespace separated)
- URL,expected_code (comma separated)

Example `image_urls.txt` lines:

```
https://example.com/path/image1.jpg
https://example.com/path/image2.jpg VA18313
https://example.com/path/image3.jpg,ED12345
```

Behaviour:
- If an expected code is provided and Tesseract OCR is available, the script will run OCR on the downloaded image and only accept/save images where the code appears on the image. Rejected images are saved under `downloaded_images/rejected/` for manual review.
- If OCR/Tesseract is not available, the script will save images but will print a warning that verification was skipped.

Double-click runner:

- `run.bat` — Double-click to run the helper PowerShell script. The helper will try to use system Python, and if not found it can download the embeddable Python, bootstrap pip, install required packages into the project folder, and run `download_images.py`.

Manual setup (recommended for maintainers):

1. Install Python 3.10+ from https://python.org and check "Add Python to PATH" in the installer.
2. From the project folder run:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python .\download_images.py
```

OCR / Tesseract note:
- The Python package `pytesseract` requires the Tesseract OCR binary to be installed on the system to function. On Windows you can install Tesseract from:
	https://github.com/tesseract-ocr/tesseract/releases (choose an installer for your platform) or via chocolatey: `choco install tesseract`.
- If you don't want to install Tesseract system-wide, the script will still run but skip verification.

If you'd like, I can also produce a fully self-contained bundle that downloads the embeddable Python and (optionally) Tesseract at first-run so the intern only needs to double-click `run.bat`.

<!-- Background removal support removed -->
=======
# Bulk-Image-Downloader
>>>>>>> 8b0e4cb7ed9f670e4265634aafc901d7c2106a24
