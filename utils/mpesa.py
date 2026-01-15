import requests
import base64
from datetime import datetime
import os
import json

class MpesaHandler:
    def __init__(self):
        # 🟢 Get these from developer.safaricom.co.ke
        self.consumer_key = os.getenv('MPESA_CONSUMER_KEY', 'EFQszmzR5Phtfk1yhcRcxneaX8tfbAbgAEUAg2OGPvmPGpyD')
        self.consumer_secret = os.getenv('MPESA_CONSUMER_SECRET', 'O1dygLmmNDNZx9eQdk58ck24OcFpHltPSUrA9CVxwYCEiego1oDdGHORuIZvbbbw')
        self.passkey = os.getenv('MPESA_PASSKEY', 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919') # Default Sandbox Passkey
        self.shortcode = os.getenv('MPESA_SHORTCODE', '174379') # Default Sandbox Paybill
        self.base_url = "https://sandbox.safaricom.co.ke"

    def get_access_token(self):
        url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
        response = requests.get(url, auth=(self.consumer_key, self.consumer_secret))
        if response.status_code == 200:
            return response.json()['access_token']
        raise Exception("Failed to get M-Pesa Token")

    def initiate_stk_push(self, phone_number, amount, account_reference):
        token = self.get_access_token()
        url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_str = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode('utf-8')

        # Ensure phone starts with 254
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # 🟢 CRITICAL: This URL MUST be your live Render URL
        callback_url = "https://homehub-project.onrender.com/api/payments/callback"

        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone_number,
            "PartyB": self.shortcode,
            "PhoneNumber": phone_number,
            "CallBackURL": callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": "Rent Payment"
        }

        response = requests.post(url, json=payload, headers=headers)
        return response.json()