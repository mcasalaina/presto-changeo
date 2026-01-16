cd /d "%~dp0backend"
call venv\Scripts\activate
pip install -r requirements.txt --quiet
python -m uvicorn main:app --reload
