from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime, timedelta
import time
import os
import json
import gspread
import pytz
from oauth2client.service_account import ServiceAccountCredentials

ist = pytz.timezone('Asia/Kolkata')
now_ist = datetime.now(ist)

print(now_ist.strftime('%Y-%m-%d %H:%M:%S %Z%z'))  # Output with timezone

with open("slack-remainder-c546d07d7770.json", "w") as f:
    f.write(os.getenv("GOOGLE_CREDENTIALS"))

# Auth
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('slack-remainder-c546d07d7770.json', scope)
client = gspread.authorize(creds)

sheet = client.open("Slack Remainder Bot").sheet1
message = sheet.cell(1, 2).value  # Get message from row 1, col 2
# day = sheet.cell(2, 2).value  # Get day from row 2, col 2 (commented out, not used anymore)
hour = sheet.cell(2, 2).value  # Get hour from row 2, col 2
min = sheet.cell(3, 2).value  # Get minute from row 3, col 2


# === 🔐 YOUR BOT TOKEN HERE ===
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

client = WebClient(token=SLACK_BOT_TOKEN)

# === 🧾 CONFIGURATION ===
# target_day = day     # Day to send message (Removed day logic)
target_hour = int(hour)           # Hour to send (24h format)
target_minute = int(min)         # Minute to send
message_to_send = message  # Your message

# === 🔍 GET USERS (Filter Bots + Deactivated) ===
def get_all_user_ids():
    try:
        response = client.users_list()
        user_ids = []
        for user in response['members']:
            if not user['is_bot'] and not user['deleted'] and user.get('id') != 'USLACKBOT':
                user_ids.append(user['id'])
        return user_ids
    except SlackApiError as e:
        print(f"Failed to fetch users: {e.response['error']}")
        return []

# === 📤 SCHEDULE DM TO USER ===
def schedule_dm(user_id, message_text, post_at_ts):
    try:
        im = client.conversations_open(users=user_id)
        channel_id = im['channel']['id']
        response = client.chat_scheduleMessage(
            channel=channel_id,
            text=message_text,
            post_at=post_at_ts
        )
        print(f"✅ Scheduled DM for {user_id} at {datetime.fromtimestamp(post_at_ts)}")
    except SlackApiError as e:
        print(f"❌ Error scheduling message to {user_id}: {e.response['error']}")

# === ⏰ FIND NEXT TARGET TIME ===
# Removed day check, just use today's date for scheduled time
def get_today_scheduled_time(hour, minute):
    now = datetime.now(ist)
    target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target_time < now:
        # If time already passed today, schedule for tomorrow
        target_time += timedelta(days=1)
    return int(target_time.timestamp())

# === 🧠 MAIN EXECUTION ===
post_at = get_today_scheduled_time(target_hour, target_minute)
print(f"⏳ Scheduling for {target_hour}:{str(target_minute).zfill(2)} today or tomorrow")
print(f"🕒 Unix timestamp: {post_at} ({datetime.fromtimestamp(post_at)})")

user_ids = ["U08T3KBBQAH"]  # Replace with get_all_user_ids() to DM everyone

# # dont use this line until and unless you are confirm that your code runs properly, if this is runned, all the people in organization will receive the message
# user_ids = get_all_user_ids() 

print(f"📨 Sending to {len(user_ids)} user(s)...")
for user_id in user_ids:
    schedule_dm(user_id, message_to_send, post_at)
    time.sleep(0.5)

print("🎯 All messages scheduled.")
