@echo off
REM Create venv with Python 3.12
py -3.12 -m venv venv
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo Setup complete! Next steps:
echo 1. Copy .env.example to .env and add your GROQ_API_KEY
echo 2. Run: python ingest.py
echo 3. Run: streamlit run streamlit_app.py
