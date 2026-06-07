# Pre-Submission QA Report

Project: Nassau Candy Product Line Profitability & Margin Intelligence Platform  
Version reviewed: v52.0

## Checks Completed

- Python syntax check passed for `app.py` and all files in `utils/`.
- Default CSV dataset loaded successfully.
- Data cleaning pipeline produced 10,194 valid records.
- Factory mapping validated: 0 unmapped products in the default dataset.
- Product, division, factory, monthly, region, Pareto, and risk summaries generated successfully.
- PDF report generation tested and returned valid PDF bytes.
- Risk Command Center raw HTML rendering issue verified as fixed in the code path.
- Plotly chart toolbar removal is enabled through chart render config.
- Export generation is click-triggered/cached for better Reports page loading performance.

## Functional Coverage

- Data cleaning and validation: Complete
- Gross margin, profit per unit, revenue contribution, profit contribution: Complete
- Product-level profitability ranking: Complete
- Division performance analysis: Complete
- Cost vs margin diagnostics: Complete
- Pareto 80/20 analysis: Complete
- Factory intelligence and map-ready coordinates: Complete
- Risk scoring and executive recommendations: Complete
- CSV, Excel, and PDF exports: Complete
- Dataset upload/import box: Complete
- Dark neon dashboard UI and loader: Complete

## Final Notes Before Submission

1. Run locally using `RUN_APP.bat` or `streamlit run app.py --server.address localhost --server.port 8501`.
2. Open only `http://localhost:8501` or `http://127.0.0.1:8501`. Do not use the external URL.
3. Test all sidebar modules once after extraction.
4. On Windows, if the browser shows an old version, run `streamlit cache clear` and hard refresh with `Ctrl + F5`.
5. Ensure dependencies are installed using `pip install -r requirements.txt`.
