import sys

def extract_pdf(path):
    try:
        import fitz
        doc = fitz.open(path)
        with open("pdf_text.txt", "w", encoding="utf-8") as f:
            for page in doc:
                f.write(page.get_text())
        print("Extracted using PyMuPDF (fitz)")
        return
    except ImportError:
        pass

    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(path)
        with open("pdf_text.txt", "w", encoding="utf-8") as f:
            for page in reader.pages:
                f.write(page.extract_text() + "\n")
        print("Extracted using PyPDF2")
        return
    except ImportError:
        pass

    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            with open("pdf_text.txt", "w", encoding="utf-8") as f:
                for page in pdf.pages:
                    f.write(page.extract_text() + "\n")
        print("Extracted using pdfplumber")
        return
    except ImportError:
        pass

    print("No suitable PDF library found. Please install PyMuPDF, PyPDF2, or pdfplumber.")

extract_pdf(sys.argv[1])
