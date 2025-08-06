# pdf_processor.py

import pdfplumber
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import os
import hashlib
from concurrent.futures import ThreadPoolExecutor


DEBUG = False  # Set True to see logs


def get_file_hash(file_path: str):
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def is_text_based_page(pdfplumber_page):
    return bool(pdfplumber_page.extract_text())


def clean_text(text):
    return ' '.join(text.replace('\n', ' ').split())


def convert_pdf_page_to_image(pdf_path, page_number, dpi=200):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_number)
    pix = page.get_pixmap(dpi=dpi)
    img_bytes = pix.tobytes("png")
    return Image.open(io.BytesIO(img_bytes))


def ocr_page_image(args):
    pdf_path, page_number = args
    image = convert_pdf_page_to_image(pdf_path, page_number)
    text = pytesseract.image_to_string(image)
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    chunks = []
    if text.strip():
        chunks.append({
            "type": "ocr_text",
            "source": os.path.basename(pdf_path),
            "page_number": page_number + 1,
            "text": clean_text(text)
        })

    # Extract row-like table text from OCR
    rows = []
    for i in range(len(data['text'])):
        word = data['text'][i]
        if word.strip():
            rows.append(word)

    if rows:
        table_text = ' | '.join(rows)
        chunks.append({
            "type": "table",
            "source": os.path.basename(pdf_path),
            "page_number": page_number + 1,
            "row_index": 0,
            "text": "",
            "table_text": clean_text(table_text)
        })

    return chunks


def extract_text_and_tables_from_text_pdf(file_path, filename):
    chunks = []
    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            if is_text_based_page(page):
                text = clean_text(page.extract_text() or "")
                if text:
                    chunks.append({
                        "type": "text",
                        "source": filename,
                        "page_number": page_num,
                        "text": text
                    })

                tables = page.extract_tables()
                if tables:
                    for table_index, table in enumerate(tables):
                        for row_index, row in enumerate(table):
                            if row and any(cell and cell.strip() for cell in row):
                                row_text = clean_text(' | '.join(cell.strip() if cell else '' for cell in row))
                                chunks.append({
                                    "type": "table",
                                    "source": filename,
                                    "page_number": page_num,
                                    "row_index": row_index,
                                    "text": "",
                                    "table_text": row_text
                                })
    return chunks


def extract_text_and_tables_from_scanned_pdf(file_path, filename):
    chunks = []
    doc = fitz.open(file_path)
    page_numbers = list(range(len(doc)))

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(ocr_page_image, [(file_path, p) for p in page_numbers]))

    for page_chunks in results:
        chunks.extend(page_chunks)

    return chunks


def process_pdf(file_path: str):
    filename = os.path.basename(file_path)
    all_chunks = []

    try:
        # Try text-based processing first
        text_chunks = extract_text_and_tables_from_text_pdf(file_path, filename)
        if text_chunks:
            if DEBUG:
                print("[DEBUG] Processed as text-based PDF")
            all_chunks.extend(text_chunks)
        else:
            if DEBUG:
                print("[DEBUG] No text found, switching to OCR")
            ocr_chunks = extract_text_and_tables_from_scanned_pdf(file_path, filename)
            all_chunks.extend(ocr_chunks)

    except Exception as e:
        print(f"[ERROR] Failed to process PDF: {e}")

    return all_chunks

__all__ = ["process_pdf", "get_file_hash"]
