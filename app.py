from pymongo import MongoClient
import os
from bson import ObjectId
from datetime import datetime
import requests
import schedule
from pytz import timezone
import time
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]


# Get today's date range
today_start = datetime.combine(datetime.today(), datetime.min.time())
today_end = datetime.combine(datetime.today(), datetime.max.time())

# Create query to count documents created today
query = {
    "_id": {
        "$gte": ObjectId.from_datetime(today_start),
        "$lt": ObjectId.from_datetime(today_end)
    }
}

pipeline = [
    {
        "$group": {
            "_id": { "$dateToString": { "format": "%Y-%m-%d", "date": "$createdAt" } },
            "count": { "$sum": 1 }
        }
    },
    { "$sort": { "_id": 1 } }  # Sort by date
]

def job():
    try:
        today_count = collection.count_documents(query)
        total_count = list(collection.aggregate(pipeline))

        payload = {
            "text": f"""
                    Agent Built Today: {today_count}
Agent Built Overall: {total_count[0]['count']}
                    """}

        webhook_url = os.getenv("WEBHOOK_URL")

        response = requests.post(webhook_url, json=payload)
        if response.status_code == 200:
            print("Message sent successfully!")
        else:
            print(f"Failed to send message. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")


def schedule_task():
    # Convert IST to your local timezone
    ist_timezone = timezone('Asia/Kolkata')
    now = datetime.now(ist_timezone)
    schedule.every().day.at("22:30").do(job)  # 00:30 is 12:30 AM in 24-hour format

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    schedule_task()
