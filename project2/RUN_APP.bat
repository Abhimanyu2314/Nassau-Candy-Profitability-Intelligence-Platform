@echo off
cd /d "%~dp0"
echo Starting Nassau Candy Profitability Intelligence Platform...
echo.
echo Opening local browser URL: http://localhost:8501
echo.
start "" http://localhost:8501
streamlit run app.py --server.headless false --server.address localhost --server.port 8501
pause
