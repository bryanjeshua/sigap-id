"""
Patch Streamlit's static index.html to inject Dicoding verification meta tag.
Runs once at container startup before Streamlit boots.
"""
from pathlib import Path
import streamlit as st

try:
    index = Path(st.__file__).parent / "static" / "index.html"
    html = index.read_text(encoding="utf-8")
    meta = '<meta name="dicoding:email" content="salmakurniadewi@gmail.com"/>'
    if "dicoding:email" not in html:
        html = html.replace("<head>", f"<head>{meta}", 1)
        index.write_text(html, encoding="utf-8")
        print(">>> Dicoding meta tag injected into Streamlit static HTML")
    else:
        print(">>> Dicoding meta tag already present")
except Exception as e:
    print(f">>> Meta tag injection failed (continuing): {e}")
