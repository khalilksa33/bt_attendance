import os
from pathlib import Path
from dotenv import load_dotenv
from zk import ZK
from frappeclient import FrappeClient

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Test Biometric Connection
try:
    zk = ZK(os.getenv("BIOMETRIC_IP"), port=int(os.getenv("BIOMETRIC_PORT")))
    conn = zk.connect()
    print("✅ Biometric Machine: Connected")
    conn.disconnect()
except Exception as e:
    print(f"❌ Biometric Machine: {e}")

# Test ERPNext Connection
try:
    client = FrappeClient(os.getenv("ERP_URL"), os.getenv("ERP_API_KEY"), os.getenv("ERP_API_SECRET"))
    # Try to fetch one employee
    res = client.get_list('Employee', limit=1)
    print("✅ ERPNext API: Connected")
except Exception as e:
    print(f"❌ ERPNext API: {e}")