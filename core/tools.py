from langchain.tools import tool
from core.db import (
    get_order,
    update_order_status,
    get_available_agent,
    update_delivery_issue,
)


@tool
def check_order_delivery_status(order_id: str) -> str:
    """
    Check the delivery status of an order.

    Args:
        order_id (str): The ID of the order.

    Returns:
        str: Delivery status message.
    """
    if not order_id:
        return "Please provide an order ID."
    order = get_order(order_id)
    if not order:
        return "Order not found."
    if order["order_status"] == "Delivered":
        return f"Your order {order_id} was delivered on {order['deliveryDate']}."
    return f"Your order {order_id} can be cancelled."


@tool
def report_order_not_received(data: dict) -> str:
    """
    Report an order that was not received.

    Args:
        data (dict): Dictionary with 'order_id' key.

    Returns:
        str: Confirmation of issue report.
    """
    order_id = data.get("order_id")
    if not order_exists(order_id):
        return "Order not found. Please provide a valid order ID."
    return f"Order {order_id} has been flagged for 'not received'. Our support team will investigate and reach out shortly."


@tool
def report_wrong_or_missing_items(data: dict) -> str:
    """
    Report wrong or missing items in an order.

    Args:
        data (dict): Dictionary with 'order_id' and 'issue' keys.

    Returns:
        str: Confirmation of issue report.
    """
    order_id = data.get("order_id")
    issue = data.get("issue")
    if not order_exists(order_id):
        return "Order not found. Please provide a valid order ID."
    return f"Issue reported for order {order_id}: {issue}. Our team will verify and respond shortly."


@tool
def report_payment_issue(data: dict) -> str:
    """
    Report a payment issue such as failure or duplicate charge.

    Args:
        data (dict): Dictionary with 'transaction_id' and 'issue_type' keys.

    Returns:
        str: Confirmation of payment issue report.
    """
    transaction_id = data.get("transaction_id")
    issue_type = data.get("issue_type")
    if not transaction_id:
        return "Please provide a valid transaction ID."
    return f"Payment issue '{issue_type}' for transaction {transaction_id} has been reported. Our finance team will look into it."


@tool
def request_address_change(data: dict) -> str:
    """
    Request a change in the delivery address for an order.

    Args:
        data (dict): Dictionary with 'order_id' and 'new_address' keys.

    Returns:
        str: Confirmation of address change request.
    """
    order_id = data.get("order_id")
    new_address = data.get("new_address")
    if not order_exists(order_id):
        return "Order not found. Please provide a valid order ID."
    return f"Request received to change delivery address for order {order_id}. We’ll update you once it’s processed."


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
        return "Order not found."
    if order["order_status"] in ["Cancelled"]:
        return "This order cannot be canceled as it is already cancelled."
    if order["order_status"] in ["Completed", "Delivered"]:
        return "This order cannot be canceled as it is already Delivered."
    update_order_status(order_id, "cancelled")
    return f"Order {order_id} has been canceled successfully."


@tool
def support_login_signup(issue: str) -> str:
    """
    Assist with login or signup issues.

    Args:
        issue (str): Description of the login/signup issue.

    Returns:
        str: Support response.
    """
    return f"Our support team will assist you with: {issue}. Please check your email or phone for verification links if applicable."


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
        return "Order not found."
    if order["vendor_status"] == "Cancelled":
        return "Your refund request is eligible and will be processed shortly."
    elif order["order_status"] == "Delivered":
        return "Since the order was delivered, it is not eligible for a refund."
    return "Please wait for vendor confirmation to process refund."


@tool
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
def report_delivery_issue(data: dict) -> str:
    """
    Report an issue with the delivery personnel.

    Args:
        data (dict): Dictionary with 'order_id' and 'issue' keys.

    Returns:
        str: Confirmation of delivery issue report.
    """
    order_id = data.get("order_id")
    issue = data.get("issue")
    if not order_exists(order_id):
        return "Order not found. Please provide a valid order ID."
    update_delivery_issue(order_id, issue)
    return f"We’re sorry to hear that. Your issue for order {order_id} has been logged: {issue}. Our support team will take immediate action."


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
        return "Order not found. Please provide a valid order ID."
    return f"Expected delivery time for order {order_id} takes around 2 - 3 hours."


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
    return bool(order)
