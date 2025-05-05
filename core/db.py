from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from models.delivery_issue import DeliveryIssue

# MongoDB client setup
client = MongoClient(
    "mongodb+srv://bmdpedevops:q021jD5vfWIKESJu@grocify.vtnyo.mongodb.net/"
)
db = client["vendors"]
orders = db["orders"]
users = db["users"]
delivery_issues = db["delivery_issues"]

msgs_db = client["chat_partner"]
messages_collection = msgs_db["messages"]


# Fetch order details
def get_order(order_id: str):
    return orders.find_one({"order_id": order_id})


# Update order status
def update_order_status(order_id: str, status: str):
    # Check if the order exists
    if not get_order(order_id):
        return
    # Update the order status
    orders.update_one({"order_id": order_id}, {"$set": {"order_status": status}})


# Update delivery issue
def update_delivery_issue(order_id: str, issue: str):
    orders.update_one({"order_id": order_id}, {"$set": {"delivery_issue": issue}})


# Fetch available support agent
def get_available_agent():
    return users.find_one({"available": True})
