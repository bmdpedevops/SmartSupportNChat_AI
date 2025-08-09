from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from models.delivery_issue import DeliveryIssue

client = MongoClient(
    "mongodb+srv://bmdpedevops:q021jD5vfWIKESJu@grocify.vtnyo.mongodb.net/"
)
db = client["vendors"]
orders = db["orders"]
users = db["users"]
delivery_issues = db["delivery_issues"]

msgs_db = client["chat_partner"]
users_collection = users
messages_collection = msgs_db["messages"]
friendrequests_collection = msgs_db["friendrequests"]
products_collection = db["items"]


def get_order(order_id: str):
    print(f"order_id for orders: {order_id}")
    res = orders.find_one({"order_id": str(order_id).strip()})
    # print("orders:", res)
    return res


def get_orders_by_user(user_id: str):
    print(f"user_id for orders: {user_id}")
    return orders.find({"customer_id": user_id})


def get_orders_by_status(status: str):
    return orders.find({"order_status": status})


def update_order_status(order_id: str, status: str):
    if not get_order(order_id):
        return
    orders.update_one({"order_id": order_id}, {"$set": {"order_status": status}})


def update_delivery_issue(order_id: str, issue: str):
    orders.update_one({"order_id": order_id}, {"$set": {"delivery_issue": issue}})


def get_available_agent():
    return users.find_one({"available": True})


def get_order_items(order_id: dict):
    response = ""
    for item in order_id["cart"]:
        item_id = item["item_id"]
        product = products_collection.find_one({"_id": ObjectId(item_id)})
        response += f"{product['item_name']}: ${item['quantity']}\n"

    return response
