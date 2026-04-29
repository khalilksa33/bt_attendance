import pandas as pd
from zk import ZK
import requests
from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Load env vars
erp_url = os.getenv("ERP_URL")
api_key = os.getenv("ERP_API_KEY")
api_secret = os.getenv("ERP_API_SECRET")

print("Fetching raw biometric data...")
try:
    zk = ZK('192.168.8.4', port=4370, timeout=5)
    conn = zk.connect()
    attendance = conn.get_attendance()
    start_date = datetime(2026, 1, 1)
    end_date = datetime(2026, 3, 31, 23, 59, 59)
    filtered_attendance = [{'user_id': record.user_id, 'timestamp': record.timestamp} for record in attendance if start_date <= record.timestamp <= end_date]
    df_bio = pd.DataFrame(filtered_attendance)
    print("Raw Biometric Data:")
    print(df_bio.to_string())
    conn.disconnect()
except Exception as e:
    print(f"Error fetching biometric data: {e}")

print("\nFetching raw ERP employee data...")
try:
    url = erp_url + '/api/resource/Employee'
    headers = {'Authorization': f'token {api_key}:{api_secret}'}
    params = {
        'fields': '["employee_name", "attendance_device_id", "department", "designation"]',
        'limit_page_length': 1000
    }
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()['data']
        df_erp = pd.DataFrame(data)
        print("Raw ERP Employee Data:")
        print(df_erp.to_string())
    else:
        print(f"ERP API Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"Error fetching ERP data: {e}")

print("\nRaw data fetch complete.")