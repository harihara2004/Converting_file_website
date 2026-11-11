import io
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image

st.set_page_config(page_title="File Converter", page_icon="🔄", layout="centered")
st.title("🔄 File Converter")
st.caption("Word → PDF  |  PNG/BMP → JPG  |  JSON → CSV")


# ---------------------------------------------------------------- converters
def word_to_pdf(uploaded) -> bytes:
    """Convert .docx/.doc to PDF.
    1) LibreOffice (soffice) if installed  2) docx2pdf (needs MS Word) as fallback."""
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / uploaded.name
        src.write_bytes(uploaded.getvalue())
        out_pdf = src.with_suffix(".pdf")

        soffice = shutil.which("soffice") or shutil.which("libreoffice")
        if not soffice:
            for p in (
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
                "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            ):
                if os.path.exists(p):
                    soffice = p
                    break

        if soffice:
            subprocess.run(
                [soffice, "--headless", "--convert-to", "pdf",
                 "--outdir", tmp, str(src)],
                check=True, capture_output=True, timeout=180,
            )
        else:
            try:
                from docx2pdf import convert
                try:  # needed on Windows when running inside a thread
                    import pythoncom
                    pythoncom.CoInitialize()
                except ImportError:
                    pass
                convert(str(src), str(out_pdf))
            except Exception as e:
                raise RuntimeError(
                    "No converter available. Install LibreOffice "
                    "(https://www.libreoffice.org) or Microsoft Word + "
                    f"`pip install docx2pdf`. Details: {e}"
                )

        if not out_pdf.exists():
            raise RuntimeError("Conversion failed - PDF was not created.")
        return out_pdf.read_bytes()


def image_to_jpg(uploaded, quality: int) -> bytes:
    img = Image.open(uploaded)
    # JPG has no transparency -> flatten onto white
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        img = bg
    else:
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def json_to_csv(uploaded) -> bytes:
    data = json.load(uploaded)
    if isinstance(data, dict):
        # a dict holding one list of records -> use that list
        lists = [v for v in data.values() if isinstance(v, list)]
        data = lists[0] if len(lists) == 1 else [data]
    df = pd.json_normalize(data)  # flattens nested objects
    return df.to_csv(index=False).encode("utf-8-sig"), df


# ---------------------------------------------------------------------- UI
tab1, tab2, tab3 = st.tabs(["📄 Word → PDF", "🖼️ PNG/BMP → JPG", "🧾 JSON → CSV"])

with tab1:
    files = st.file_uploader("Upload Word file(s)", type=["docx", "doc"],
                             accept_multiple_files=True, key="word")
    if files and st.button("Convert to PDF", key="btn_word"):
        for f in files:
            with st.spinner(f"Converting {f.name}..."):
                try:
                    pdf = word_to_pdf(f)
                    st.success(f"{f.name} converted")
                    st.download_button(
                        f"⬇️ Download {Path(f.name).stem}.pdf", pdf,
                        file_name=f"{Path(f.name).stem}.pdf",
                        mime="application/pdf", key=f"dl_word_{f.name}")
                except Exception as e:
                    st.error(f"{f.name}: {e}")

with tab2:
    files = st.file_uploader("Upload image(s)", type=["png", "bmp"],
                             accept_multiple_files=True, key="img")
    quality = st.slider("JPG quality", 10, 100, 90)
    if files and st.button("Convert to JPG", key="btn_img"):
        for f in files:
            try:
                jpg = image_to_jpg(f, quality)
                st.image(jpg, caption=f.name, width=250)
                st.download_button(
                    f"⬇️ Download {Path(f.name).stem}.jpg", jpg,
                    file_name=f"{Path(f.name).stem}.jpg",
                    mime="image/jpeg", key=f"dl_img_{f.name}")
            except Exception as e:
                st.error(f"{f.name}: {e}")

with tab3:
    f = st.file_uploader("Upload JSON file", type=["json"], key="json")
    if f and st.button("Convert to CSV", key="btn_json"):
        try:
            csv_bytes, df = json_to_csv(f)
            st.dataframe(df.head(50))
            st.download_button(
                "⬇️ Download CSV", csv_bytes,
                file_name=f"{Path(f.name).stem}.csv", mime="text/csv")
        except Exception as e:
            st.error(f"Could not convert: {e}")
