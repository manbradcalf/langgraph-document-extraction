import pdfplumber
import pytesseract


def read_pdf(pdf_path: str):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            page_text = page.extract_text()

            if not page_text or len(page_text.strip()) == 0:
                print(f"No text found on page {page_num + 1}, using OCR...")
                page_image = page.to_image(resolution=300)
                page_text = pytesseract.image_to_string(page_image.original)

            text += page_text + "\n\n"
    return text
