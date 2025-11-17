import streamlit as st
import nltk
import os

@st.cache_resource
def inicializar_nltk():
    """
    Inicializa os recursos do NLTK, baixando-os se necessário.
    """
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')