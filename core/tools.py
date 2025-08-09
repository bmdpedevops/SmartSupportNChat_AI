from langchain.tools import tool
from core.db import (
    get_order,
    update_order_status,
    get_available_agent,
    update_delivery_issue,
    get_orders_by_user,
    get_order_items,
)
from models.query_model import MenuItemResponse
from core.db import db
import json

orders_collection = db["orders"]
products_collection = db["items"]
support_collection = db["support_tickets "]


@tool
def explain_capabilities(_=None) -> str:
    """
    Explain what the assistant can do using its available tools.
    """
    return """
I can help you with a variety of customer support tasks. Here's what I can do:

📦 **Order & Delivery**
- Check your order's delivery status
- Get expected delivery time
- Report delivery issues
- Report missing or wrong items
- Change delivery address
- Report order not received

💸 **Refunds & Cancellations**
- Check refund eligibility
- Cancel an order
- Report payment issues

🔍 **Product & Order Info**
- Search for products
- Check order status
- Get full order details

Just ask what you need help with!
"""


@tool
def check_order_delivery_status(order_id: str) -> str:
    """
    Check the delivery status of an order.

    Args:
        order_id (str): The ID of the order.

    Returns:
        str: Delivery status message.
    """
    try:
        if not order_id:
            return "Tool output: Please provide an order ID."

        # Remove leading and trailing quotes (single or double)
        order_id = order_id.strip("\"'")

        order = get_order(order_id)
        if not order:
            return "Tool output: Order not found."

        return f"Tool output: Order status: {order['order_status']}"

    except Exception as e:
        return "Tool output: Invalid input format. Use 'order_id'."


# @tool
# def get_orders_by_item_names_tool(input: str) -> str:
#     """
#     Search for orders by item names.
#     Args:
#         input (str): JSON string with item_names (comma-separated string) and user_id.
#         Example: '{"item_names": "Bread,Butter", "user_id": "..."}'
#     Returns:
#         str: List of matching order IDs or error message.
#     """
#     import json

#     try:
#         data = json.loads(input)

#         item_names_raw = data.get("item_names")
#         # remove the quotes from the string
#         item_names_raw = item_names_raw.replace("'", "")
#         print(f"item_names_raw: {item_names_raw}")
#         if not item_names_raw:
#             return "Missing required field: item_names"

#         item_names = [name.strip() for name in item_names_raw.split(",")]
#         print(f"item_names: {item_names}")
#         user_id = data.get("user_id")
#         if not user_id:
#             return "Missing required field: user_id"

#         # Find matching item_ids
#         item_docs = list(
#             products_collection.find(
#                 {"item_name": {"$in": item_names}}, {"_id": 1, "item_name": 1}
#             )
#         )
#         item_ids = [str(doc["_id"]) for doc in item_docs]
#         found_item_names = [doc["item_name"] for doc in item_docs]
#         missing_items = [name for name in item_names if name not in found_item_names]

#         if missing_items:
#             return f"Some items not found: {', '.join(missing_items)}. Please verify the item names."

#         if not item_ids:
#             return "No items found with the given names."

#         # Find orders for this customer and those items
#         matching_orders = orders_collection.find(
#             {"customer_id": user_id, "cart.item_id": {"$in": item_ids}}, {"order_id": 1}
#         )

#         order_ids = [order["order_id"] for order in matching_orders]
#         return (
#             f"Matching order IDs: {order_ids}"
#             if order_ids
#             else "No matching orders found."
#         )

#     except json.JSONDecodeError:
#         return "Invalid input format. Please provide a valid JSON string with item_names and user_id."
#     except Exception as e:
#         return f"Error: {str(e)}"


@tool
def search_products(product_name: str):
    """Search a product by name and return structured product details."""
    print("product_name:", product_name)
    product_name = product_name.strip()
    product = products_collection.find_one(
        {"item_name": {"$regex": f".*{product_name}.*", "$options": "i"}}
    )
    print("product:", product)

    if not product:
        return "Tool output: Product not found."

    # Parse and serialize using Pydantic
    validated = MenuItemResponse.model_validate(product)
    return "Tool output: " + validated.model_dump_json(indent=2)


@tool
def check_order_status(order_id_user: str) -> str:
    """
    Check the status of a customer's order. Input format: 'order_id|user_id'
    """
    try:
        order_id, user_id = order_id_user.split("|")
        order_id = order_id.strip("\"'")
        user_id = user_id.strip("\"'")
        order = orders_collection.find_one(
            {"order_id": order_id, "customer_id": user_id}
        )
        if not order:
            return "Order not found for this user."
        return "Tool output: Order status: " + order["order_status"]
    except Exception:
        return "Invalid input format. Use 'order_id|user_id'."


from pydantic import BaseModel


class ReportOrderInput(BaseModel):
    order_id: str
    user_id: str


@tool
def report_order_not_received(order_id_user: str) -> str:
    """
    Report an order that was not received.Input format: 'order_id|user_id'
    """
    try:
        order_id, user_id = order_id_user.split("|")
        order_id = order_id.strip("\"'")
        user_id = user_id.strip("\"'")
        if not order_exists(order_id):
            return "Tool output: Order not found. Please provide a valid order ID."

        support_collection.insert_one(
            {"order_id": order_id, "user_id": user_id, "issue": "not received"}
        )

        return f"Tool output: Order {order_id} has been flagged for 'not received'. Our support team will investigate and reach out shortly."
    except Exception as e:
        return "Tool output: Invalid input format. Use 'order_id|user_id'."


@tool
def report_wrong_or_missing_items(data: str) -> str:
    """
    Report wrong or missing items in an order.Input format: 'order_id|user_id|issue'
    """
    try:
        order_id, user_id, issue = data.split("|")
        order_id = order_id.strip("\"'")
        user_id = user_id.strip("\"'")
        issue = issue.strip("\"'")

        if not order_exists(order_id):
            return "Tool output: Order not found. Please provide a valid order ID."
        support_collection.insert_one(
            {"user_id": user_id, "order_id": order_id, "issue": issue}
        )
        return f"Tool output: Issue reported for order {order_id}: {issue}. Our team will verify and respond shortly."
    except Exception as e:
        return "Invalid input format. Use 'order_id|user_id|issue'."


@tool
def report_payment_issue(data: str) -> str:
    """
    Report a payment issue such as failure or duplicate charge.Input format: 'transaction_id|user_id|issue_type'
    """
    try:
        transaction_id, user_id, issue_type = data.split("|")
        transaction_id = transaction_id.strip("\"'")
        user_id = user_id.strip("\"'")
        issue_type = issue_type.strip("\"'")

        if not transaction_id:
            return "Tool output: Please provide a valid transaction ID."
        support_collection.insert_one(
            {
                "user_id": user_id,
                "transaction_id": transaction_id,
                "issue_type": issue_type,
            }
        )
        return f"Tool output: Payment issue '{issue_type}' for transaction {transaction_id} has been reported. Our finance team will look into it."
    except Exception as e:
        return "Invalid input format. Use 'transaction_id|user_id|issue_type'."


@tool
def request_address_change(data: str) -> str:
    """
    Request a change in the delivery address for an order.Input format: 'order_id|new_address|user_id'
    """
    try:
        order_id, new_address, user_id = data.split("|")
        order_id = order_id.strip("\"'")
        new_address = new_address.strip("\"'")
        user_id = user_id.strip("\"'")
        if not order_exists(order_id):
            return "Tool output: Order not found. Please provide a valid order ID."
        support_collection.insert_one(
            {"user_id": user_id, "order_id": order_id, "new_address": new_address}
        )
        return f"Tool output: Request received to change delivery address for order {order_id}. We’ll update you once it’s processed."
    except Exception as e:
        return "Invalid input format. Use 'order_id|new_address|user_id'."


@tool
def cancel_order(order_id: str) -> str:
    """
    Cancel an order if it's not already delivered or canceled.

    Args:
        order_id (str): The ID of the order.

    Returns:
        str: Result of cancellation attempt.
    """
    order = get_order(order_id)
    if not order:
        return "Tool output: Order not found."
    if order["order_status"] in ["Cancelled"]:
        return "Tool output: This order cannot be canceled as it is already cancelled."
    if order["order_status"] in ["Completed", "Delivered"]:
        return "Tool output: This order cannot be canceled as it is already Delivered."
    update_order_status(order_id, "cancelled")
    return f"Tool output: Order {order_id} has been canceled successfully."


@tool
def support_login_signup(data: str) -> str:
    """
    Assist with login or signup issues.Input format: 'issue|user_id'
    """
    try:
        issue, user_id = data.split("|")
        issue = issue.strip("\"'")
        user_id = user_id.strip("\"'")
        support_collection.insert_one({"issue": issue, "user_id": user_id})
        return f"Tool output:Our support team will assist you with: {issue}."
    except Exception as e:
        return "Invalid input format. Use 'issue|user_id'."


@tool
def check_refund_eligibility(order_id: str) -> str:
    """
    Check if an order is eligible for a refund.

    Args:
        order_id (str): The ID of the order.

    Returns:
        str: Refund eligibility status.
    """
    if not order_id:
        return "Please provide an order ID."
    order = get_order(order_id)
    if not order:
        return "Tool output: Order not found."
    if order["vendor_status"] == "Cancelled":
        return "Tool output : Your refund request is eligible and will be processed shortly."
    elif order["order_status"] == "Delivered":
        return "Tool output : Since the order was delivered, it is not eligible for a refund."
    return "Tool output: Please wait for vendor confirmation to process refund."


def order_not_found(order_id: str) -> str:
    """
    Handle cases where an order is not found.

    Args:
        order_id (str): The ID of the order.

    Returns:
        str: Not found message.
    """
    return "Order not found."


@tool
def escalate_to_human(query: str) -> str:
    """
    Escalate an issue to a human agent.

    Args:
        query (str): The user's query or complaint.

    Returns:
        str: Escalation status.
    """
    agent = get_available_agent()
    if agent:
        return f"Your query is being assigned to our support agent {agent['name']}."
    return "No support agents are available at the moment. Please try again later."


@tool
def report_delivery_issue(data: str) -> str:
    """
    Report an issue with the delivery personnel.Input format: 'order_id|issue
    """
    try:
        order_id, issue = data.split("|")
        order_id = order_id.strip("\"'")
        issue = issue.strip("\"'")
        if not order_exists(order_id):
            return "Tool output: Order not found. Please provide a valid order ID."
        update_delivery_issue(order_id, issue)
        return f"Tool output : We’re sorry to hear that. Your issue for order {order_id} has been logged: {issue}. Our support team will take immediate action."
    except Exception as e:
        return "Tool output: Invalid input format. Use 'order_id|issue'."


@tool
def get_expected_delivery_time(order_id: str) -> str:
    """
    Get the estimated delivery time for an order.

    Args:
        order_id (str): The ID of the order.

    Returns:
        str: Expected delivery time.
    """
    if not order_exists(order_id):
        return "Tool output: Order not found. Please provide a valid order ID."
    return f"Tool output: Expected delivery time for order {order_id} takes around 2 - 3 hours."


def order_exists(order_id: str) -> bool:
    """
    Check if an order exists in the database.

    Args:
        order_id (str): The ID of the order.

    Returns:
        bool: True if order exists, else False.
    """
    if not order_id:
        return False
    order = get_order(order_id)
    return "Tool output: Order exists" if order else "Tool output: Order not found."


from langchain.tools import tool
from pydantic import BaseModel


class GetOrdersInput(BaseModel):
    user_id: str


from langchain.tools import tool
from pydantic import BaseModel

from langchain_core.tools import InjectedToolArg, tool
from typing_extensions import Annotated


# @tool(parse_docstring=True)
# def get_orders(user_id: str) -> str:
#     """
#     Get all orders placed by a user.

#     Args:
#         user_id (str): The ID of the user.

#     Returns:
#         str: List of orders placed by the user.
#     """
#     print(f"user_id for orders: {user_id}")
#     if not user_id:
#         return "Please provide a valid user ID."

#     orders_cursor = get_orders_by_user(user_id)
#     print("orders_cursor:", orders_cursor)
#     orders_cursor = get_orders_by_user(user_id).sort("created_at", -1).limit(10)
#     orders_list = list(orders_cursor)

#     if not orders_list:
#         return f"No orders found for user {user_id}."
#     orders = []  # ✅ store list of order strings

#     for ordr in orders_list:
#         items = get_order_items(ordr)
#         print("items:", items)
#         orders.append(
#             f"Order Id : {ordr['order_id']} Order Date: {ordr['created_at']},\nOrder Items:\n{items}, order status : {ordr['order_status']} , Total: ${ordr['total_price']}\n"
#         )
#     print("orders:")
#     print("\n---\n".join(orders))

#     return "\n---\n".join(orders)  # ✅ properly join a list of strings


@tool
def get_orders_by_time(data: str) -> str:
    """
    Get all orders placed by a user.

    Args:
        data (dict): Dictionary with 'user_id' and 'time' keys.

    Returns:
        str: List of orders placed by the user.
    """
    print(f"data for orders: {data}")
    data = eval(data)
    user_id = data.get("user_id")
    time = data.get("time")
    if not user_id:
        return "Please provide a valid user ID."
    orders_cursor = get_orders_by_user(user_id).sort("created_at", -1).limit(10)
    orders_list = list(orders_cursor)

    if not orders_list:
        return f"No orders found for user {user_id}."
    orders = []  # ✅ store list of order strings

    for ordr in orders_list:
        items = get_order_items(ordr)


@tool
def get_order_by_id(order_id: str) -> str:
    """
    Get the details of an order by its ID.

    Args:
        order_id (str): The ID of the order.

    Returns:
        str: Order details.
    """
    if not order_id:
        return "Please provide a valid order ID."

    print(f"order_id: {order_id}")
    order = get_order(order_id)
    print(f"order: {order}")

    if not order:
        return "Order not found."

    return (
        f"Tool output: Order ID: {order['order_id']}\n"
        f"Order ID: {order['order_id']}\n"
        f"Order Date: {order['created_at']}\n"
        f"Order Items:\n{get_order_items(order)}\n"
        f"Order Status: {order['order_status']}\n"
        f"Total: ${order['total_price']}"
    )
