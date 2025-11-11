from io import BytesIO
import PyPDF2
from config import NLP, STOP_WORDS, PUNCT

def extract_text_from_pdf_bytes(file_bytes) -> str:
    reader = PyPDF2.PdfReader(file_bytes)
    return "\n".join([page.extract_text() or "" for page in reader.pages])

def preprocess_text(text: str) -> str:
    text = text.lower()
    doc = NLP(text)
    tokens = [t.text for t in doc if t.text not in STOP_WORDS and t.text not in PUNCT and not t.is_space]
    return " ".join(tokens)
