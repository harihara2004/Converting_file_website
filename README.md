# File Converter (Streamlit)

## Run in VS Code
1. Open this folder in VS Code (File > Open Folder).
2. Open terminal (Ctrl + `) and create a virtual env:
   python -m venv venv
   venv\Scripts\activate        (Windows)
   source venv/bin/activate     (Mac/Linux)
3. pip install -r requirements.txt
4. streamlit run app.py
   Browser opens at http://localhost:8501

## Word -> PDF needs ONE of:
- LibreOffice installed (free, works everywhere), or
- Microsoft Word installed (Windows/Mac) - used by docx2pdf
