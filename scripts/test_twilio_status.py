import os
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')

if not account_sid or not auth_token:
    print("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be configured in your .env file.")
    exit(0)

client = Client(account_sid, auth_token)

print("="*60)
print("TWILIO ACCOUNT DIAGNOSTIC")
print("="*60)
print(f"Account SID: {account_sid}")

# Check incoming phone numbers
numbers = client.incoming_phone_numbers.list()
print(f"Assigned Twilio Phone Numbers: {[n.phone_number for n in numbers]}")

# Check verified caller IDs
caller_ids = client.outgoing_caller_ids.list()
print(f"Verified Caller IDs (India/US): {[c.phone_number for c in caller_ids]}")

# Check recent messages
messages = client.messages.list(limit=5)
print(f"Recent Messages in Account: {len(messages)}")

print("="*60)
