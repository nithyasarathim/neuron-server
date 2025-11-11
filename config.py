import os
import nltk
import string
import spacy
from sentence_transformers import SentenceTransformer

# ---------------------- Directories ----------------------
BASE_DIR = "data"
RESUMES_DIR = os.path.join(BASE_DIR, "resumes")
JDS_DIR = os.path.join(BASE_DIR, "job_descriptions")
RESUME_META = os.path.join(BASE_DIR, "resumes_meta.json")
JD_META = os.path.join(BASE_DIR, "jds_meta.json")

os.makedirs(RESUMES_DIR, exist_ok=True)
os.makedirs(JDS_DIR, exist_ok=True)

# ---------------------- NLP Setup ----------------------
nltk.download("stopwords", quiet=True)
STOP_WORDS = set(nltk.corpus.stopwords.words("english"))
PUNCT = set(string.punctuation)

try:
    NLP = spacy.load("en_core_web_sm")
except:
    from spacy.cli import download as spacy_download
    spacy_download("en_core_web_sm")
    NLP = spacy.load("en_core_web_sm")

# ---------------------- Sentence Transformer ----------------------
ST_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
