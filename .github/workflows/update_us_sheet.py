name: Update US Stocks to Google Sheet
on:
  schedule:
    - cron: '30 22 * * 1-5'
  workflow_dispatch:
jobs:
  update-sheet:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repo
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install Libraries
        run: pip install gspread oauth2client pandas requests yfinance lxml html5lib

      - name: Run Python Script
        env:
          GCP_CREDENTIALS: ${{ secrets.GCP_CREDENTIALS }}
        # यहाँ हमने आपकी फाइल का सही नाम 'update_us_sheet.py' डाल दिया है
        run: python us_sheet.py
