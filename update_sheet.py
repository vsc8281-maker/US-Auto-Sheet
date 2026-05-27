import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import os
import json

# 1. Credentials Setup
creds_json = os.environ.get('GCP_CREDENTIALS')
if not creds_json:
    print("ERROR: GCP_CREDENTIALS secret missing!")
    exit(1)

creds_dict = json.loads(creds_json)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# ⚠️ अपनी US वाली गूगल शीट की ID यहाँ डालें
spreadsheet_id = "1Ub7LjwdrIcEHW48qv-cQCxbd6SN3uspqqaL3fH6_a5w"

try:
    ws_volume = client.open_by_key(spreadsheet_id).worksheet("Top 250 Stocks")
    ws_turnover = client.open_by_key(spreadsheet_id).worksheet("Top 250 Turnover")
except Exception as e:
    print(f"Sheet Connection Error: {e}")
    exit(1)

# 2. Fetch US Data (S&P 500 Stocks)
print("S&P 500 स्टॉक्स की लिस्ट निकाल रहे हैं...")
try:
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    tickers = pd.read_html(url)[0]['Symbol'].str.replace('.', '-').tolist()
    
    print("Yahoo Finance से लाइव डेटा डाउनलोड हो रहा है (इसमें 1-2 मिनट लग सकते हैं)...")
    # yfinance से आज का डेटा लाना
    df = yf.download(tickers, period='1d', progress=False)
    
    close_prices = df['Close'].iloc[-1]
    volumes = df['Volume'].iloc[-1]
    
    us_df = pd.DataFrame({'Close': close_prices, 'Volume': volumes})
    us_df.index.name = 'Symbol'
    us_df.reset_index(inplace=True)
    us_df.dropna(inplace=True)
    
    # टर्नओवर निकालना (Volume * Close Price)
    us_df['Turnover'] = us_df['Close'] * us_df['Volume']
    
    # लिस्ट A: वॉल्यूम के आधार पर टॉप 250
    df_vol = us_df.sort_values(by='Volume', ascending=False).head(250)
    data_vol = df_vol[['Symbol', 'Volume', 'Close']].round(2).values.tolist()
    
    # लिस्ट B: टर्नओवर के आधार पर टॉप 250
    df_turnover = us_df.sort_values(by='Turnover', ascending=False).head(250)
    data_turnover = df_turnover[['Symbol', 'Turnover', 'Close']].round(2).values.tolist()

except Exception as e:
    print(f"Data Fetch Error: {e}")
    exit(1)

# 3. Update Sheets
if data_vol and data_turnover:
    try:
        ws_volume.batch_clear(['A2:C251'])
        ws_volume.update('A2', data_vol)
        
        ws_turnover.batch_clear(['A2:C251'])
        ws_turnover.update('A2', data_turnover)
        
        ist_now = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime('%d-%b %H:%M')
        status_msg = f"Data Date: S&P 500 US Market | Last Update: {ist_now} (IST)"
        
        ws_volume.update('K2', [[status_msg]])
        ws_turnover.update('K2', [[status_msg]])
        
        print("SUCCESS: US मार्केट का डेटा दोनों शीट्स में सफलतापूर्वक अपडेट हो गया है!")
    except Exception as e:
        print(f"Google Sheet Update Error: {e}")
        exit(1)
else:
    print("FAILED: डेटा नहीं मिल पाया।")
