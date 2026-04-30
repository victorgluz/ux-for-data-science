import base64
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Apresentação",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

ROOT = Path(__file__).resolve().parent.parent


def inject_svgs(html: str) -> str:
    asset_dir = ROOT / "presentation_assets"

    def repl(match: re.Match[str]) -> str:
        name = match.group(1)
        p = asset_dir / name
        if not p.is_file():
            return match.group(0)
        b64 = base64.standard_b64encode(p.read_bytes()).decode("ascii")
        return f'src="data:image/svg+xml;base64,{b64}"'

    return re.sub(r'src="presentation_assets/([^"]+)"', repl, html)


html = inject_svgs((ROOT / "presentation.html").read_text(encoding="utf-8"))

components.html(html, height=940, scrolling=False)
