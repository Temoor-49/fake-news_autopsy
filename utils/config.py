
import os


def get_secret(key: str) -> str:
    """
    Loads a secret from environment variable (local)
    or Streamlit secrets (cloud deployment).
    Priority: environment variable → Streamlit secrets → empty string
    """
    # First try environment variable (works locally with .env)
    value = os.getenv(key, "")
    if value:
        return value

    # Then try Streamlit secrets (works on Streamlit Cloud)
    try:
        import streamlit as st
        value = st.secrets.get(key, "")
        if value:
            return value
    except Exception:
        pass

    return ""