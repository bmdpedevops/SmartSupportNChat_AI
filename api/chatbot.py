from fastapi import APIRouter, HTTPException
from core.memorystore import get_last_order_id, set_last_order_id
from models.query_model import QueryRequest
from core.llm import groq_llm, anthropic_llm
from core.tools import (
    check_order_delivery_status,
    check_refund_eligibility,
    cancel_order,
    escalate_to_human,
    report_delivery_issue,
    get_expected_delivery_time,
    report_wrong_or_missing_items,
    report_payment_issue,
    request_address_change,
    support_login_signup,
    report_order_not_received,
    order_exists,
    order_not_found,
    search_products,
    check_order_status,
    get_order_by_id,
    explain_capabilities,
    ask_for_order_id
)
from langchain.agents import initialize_agent, AgentType
from langchain_core.tools import Tool
from langchain_core.tools import InjectedToolArg

router = APIRouter()

from pydantic import BaseModel


class GetOrdersInput(BaseModel):
    user_id: str


from langchain.callbacks.base import AsyncCallbackHandler


class ToolUsageTracker(AsyncCallbackHandler):
    def __init__(self, user_id: str):
        self.tool_used = False
        self.user_id = user_id

    async def on_tool_start(self, serialized, input_str, **kwargs):
        self.tool_used = True
        name = (serialized or {}).get("name", "")
        if name in {"get_order_by_id", "check_order_status", "check_refund_eligibility"}:
            oid = str(input_str).strip().strip('"').strip("'")
            if oid:
                set_last_order_id(self.user_id, oid)


def build_groq_agent(user_id: str, callbacks=None):
    tools = [
        Tool(
            name="check_order_delivery_status",
            func=check_order_delivery_status,
            description="only to Check the delivery status of an order using its ID.it is not ued for checking order details",
        ),
        Tool(
            name="explain_capabilities",
            func=explain_capabilities,
            description="Use this tool when the user asks what you can do, how you can help, or for an overview of your support capabilities.",
            return_direct=True,
        ),
        Tool(
            name="check_refund_eligibility",
            func=check_refund_eligibility,
            description="only to Check if an order is eligible for a refund.it is not ued for checking order details",
        ),
        Tool(
            name="cancel_order",
            func=cancel_order,
            description="Cancel an order based on its ID.",
        ),
        Tool(
            name="escalate_to_human",
            func=escalate_to_human,
            description="Escalate the issue to a human support agent.",
        ),
        Tool(
            name="report_delivery_issue",
            func=report_delivery_issue,
            description="Report any delivery-related issues.",
        ),
        Tool(
            name="get_expected_delivery_time",
            func=get_expected_delivery_time,
            description="Get the expected delivery time for a specific order.",
        ),
        Tool(
            name="report_wrong_or_missing_items",
            func=report_wrong_or_missing_items,
            description="Report wrong or missing items in the order.",
        ),
        Tool(
            name="report_payment_issue",
            func=report_payment_issue,
            description="Report any issues related to payment.",
        ),
        Tool(
            name="request_address_change",
            func=request_address_change,
            description="Request a delivery address change for an order.",
        ),
        Tool(
            name="support_login_signup",
            func=support_login_signup,
            description="Help with login or signup issues.",
        ),
        Tool(
            name="report_order_not_received",
            func=report_order_not_received,
            description="Report that the order has not been received.",
            # return_direct=True,
        ),
        Tool(
            name="order_not_found",
            func=order_not_found,
            description="Handle cases when an order ID is not found.",
        ),
        Tool(
            name="get_order_by_id",
            func=get_order_by_id,
            description="check the order details for an order using its ID.",
            return_direct=True,
        ),
        Tool(
            name="search_products",
            func=search_products,
            description="Search for products using product names.",
        ),
        Tool(
            name="check_order_status",
            func=check_order_status,
            description="Check the current status of a specific order.",
        ),
    ]

    prefix = f"""
        You are a smart and friendly virtual assistant for customer support.
        If the users query is not related to the tools, and related to greetings or other non-tool related queries, respond with a warm and friendly welcome.
        or else use the tools or your own reasoning to provide accurate and helpful responses.
        If the request is ambiguous or needs human judgment, escalate it using the `escalate_to_human` tool.
        User ID: {user_id}
    """

    return initialize_agent(
        tools=tools,
        llm=groq_llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        agent_kwargs={"prefix": prefix},
        callbacks=callbacks or [],
        handle_parsing_errors=True,
    )


def build_agent(user_id: str, callbacks=None):
    tools = [
        Tool(
            name="ask_for_order_id",
            func=ask_for_order_id,
            description="Use ONLY when no ORDER_ID is present in the message AND there is no [CTX] ORDER_ID "
        "in the input. If [CTX] ORDER_ID exists, use it instead of asking.",
            # return_direct=True,
        ),
        Tool(
            name="check_order_delivery_status",
            func=check_order_delivery_status,
            description="Check the delivery status of an order using its ID.",
        ),
        Tool(
            name="explain_capabilities", 
            func=explain_capabilities,
            description="Use this tool when the user asks what you can do, how you can help, or for an overview of your support capabilities.",
            return_direct=True,
        ),
        Tool(
            name="check_refund_eligibility",
            func=check_refund_eligibility,
            description="Check if an order is eligible for a refund.",
        ),
        Tool(
            name="cancel_order",
            func=cancel_order,
            description="Cancel an order based on its ID.",
        ),
        Tool(
            name="escalate_to_human",
            func=escalate_to_human,
            description="Escalate the issue to a human support agent when user has complaints or needs human help.",
            return_direct=True,
        ),
        Tool(
            name="report_delivery_issue",
            func=report_delivery_issue,
            description="Report any delivery-related issues.",
        ),
        Tool(
            name="get_expected_delivery_time",
            func=get_expected_delivery_time,
            description="Get the expected delivery time for a specific order.",
        ),
        Tool(
            name="report_wrong_or_missing_items",
            func=report_wrong_or_missing_items,
            description="Report wrong or missing items in the order.",
        ),
        Tool(
            name="report_payment_issue",
            func=report_payment_issue,
            description="Report any issues related to payment.",
        ),
        Tool(
            name="request_address_change",
            func=request_address_change,
            description="Request a delivery address change for an order.",
        ),
        Tool(
            name="support_login_signup",
            func=support_login_signup,
            description="Help with login or signup issues.",
        ),
        Tool(
            name="report_order_not_received",
            func=report_order_not_received,
            description="Report that the order has not been received.",
        ),
        Tool(
            name="order_not_found",
            func=order_not_found,
            description="Handle cases when an order ID is not found.",
        ),
        Tool(
            name="get_order_by_id",
            func=get_order_by_id,
            description="Get order details using order ID.",
            return_direct=True,
        ),
        Tool(
            name="search_products",
            func=search_products,
            description="Search for products using product names.",
        ),
        Tool(
            name="check_order_status",
            func=check_order_status,
            description="Check the current status of a specific order.",
        ),
    ]

    ctx_id = get_last_order_id(user_id)
    ctx_hint = f"\nIf user doesn't specify an order id in this turn, assume {ctx_id} by default unless they explicitly give a new one.\n" if ctx_id else ""
    prefix = f"""
You are a customer support assistant. Use the available tools to help users.

IMPORTANT RULES:
- If the input contains a bracketed context like "[CTX] ORDER_ID=...", TREAT THAT AS THE ORDER ID.
- Do NOT ask for order id when [CTX] ORDER_ID is present.
- Only use ask_for_order_id when neither the message nor [CTX] provide an id.
- Prefer get_order_by_id / check_refund_eligibility with the contextual ORDER_ID.

1. If user reports order issues but no order ID provided, use ask_for_order_id tool
2. If user provides order ID (7-10 digits), use get_order_by_id tool  
3. If user asks what you can do, use explain_capabilities tool
4. Always use tools to respond, don't give direct answers
5. Follow the exact format: Thought -> Action -> Action Input
{ctx_hint}
User ID: {user_id}
"""

    return initialize_agent(
        tools=tools,
        llm=anthropic_llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        max_iterations=3,
        agent_kwargs={"prefix": prefix},
        callbacks=callbacks or [],
        early_stopping_method="generate",
        handle_parsing_errors="Please use the format:\nThought: [your reasoning]\nAction: [tool_name]\nAction Input: [input]",
    )


async def summarize_response(raw_output: str, user_query: str) -> str:
    prompt = f"""
    You are a helpful assistant. Summarize the response to the user's query interactively and conversationally.

    User query: {user_query}

    Raw tool response:
    {raw_output}
directly give the response so that i can use it to answer the user's query
    """
    response = await anthropic_llm.ainvoke(prompt)
    print(f"response in summarize_response: {response}")
    return (
        response.content if hasattr(response, "content") else str(response["response"])
    )


from typing import Literal


async def classify_intent(user_query: str) -> str:
    """
    Classifies user intent using Groq LLM as 'tool' or 'chat'.
    """
    # Quick keyword-based pre-check to avoid LLM calls for obvious cases
    query_lower = user_query.lower().strip()
    
    # Check for order ID patterns
    import re
    has_order_id = bool(re.search(r'\b\d{7,10}\b', user_query))
    
    # If contains order ID, definitely tool
    if has_order_id:
        return "tool"
    
    # Pure greetings = chat
    pure_chat = ["hi", "hello", "hey", "thanks", "thank you"]
    if query_lower in pure_chat:
        return "chat"
    
    # Order-related keywords = tool
    tool_keywords = ["order", "delivery", "refund", "cancel", "status", "issue", "problem"]
    if any(keyword in query_lower for keyword in tool_keywords):
        return "tool"
    
    # Use Groq LLM for ambiguous cases
    prompt = f"""
You are an AI assistant that classifies customer support queries into two categories:
1. "tool" - The user wants to check or take action on an order, delivery, refund, payment, account issue, or anything that needs a defined support tool.
2. "chat" - The user is just saying hi, asking what you can do, thanking, or asking a general question not tied to any tool.

Only return **one word**: either "tool" or "chat". No explanation.

Examples:
- "Where is my order?" → tool
- "Cancel my order" → tool
- "Hi" → chat
- "Thanks" → chat
- "What can you do?" → tool
- "here is the id 7251983047" → tool

Now classify this:
"{user_query.strip()}"
"""
    
    response = await groq_llm.ainvoke(prompt)
    result = response.content.strip().lower()
    return "tool" if result == "tool" else "chat"

import re

async def enhance_query_with_order_id(user_query: str) -> str:
    """
    Extract order ID from user message if present, otherwise ask for it.
    """
    # Look for order ID patterns (numbers, could be 7-10 digits)
    order_id_pattern = r'\b\d{7,10}\b'
    matches = re.findall(order_id_pattern, user_query)
    
    if matches:
        order_id = matches[0]
        print(f"Found order ID: {order_id}")
        return f"{user_query} [ORDER_ID: {order_id}]"
    
    # Check if they're asking about order but no ID found
    order_related_keywords = ["order", "delivery", "status", "refund", "cancel", "track"]
    if any(keyword in user_query.lower() for keyword in order_related_keywords):
        if "order" in user_query.lower() and not matches:
            return f"{user_query} [NOTE: Please ask for order ID if not provided]"
    
    return user_query

def clean_tool_response(response: str) -> str:
    """
    Clean tool responses to be concise and user-friendly.
    """
    # Remove "Tool output:" prefix
    response = response.replace("Tool output:", "").strip()
    
    # Remove excessive newlines
    response = re.sub(r'\n+', '\n', response)
    
    # Limit response length
    if len(response) > 500:
        response = response[:500] + "..."
    
    return response

# def enhance_query_for_agent(user_query: str) -> str:
#     """Enhance query to help agent understand context better"""
#     # Extract order ID if present
#     import re
#     order_ids = re.findall(r'\b\d{7,10}\b', user_query)
    
#     if order_ids:
#         order_id = order_ids[0]
#         return f"User query: {user_query}\nOrder ID found: {order_id}"
    
#     return user_query

def enhance_query_for_agent(user_query: str, user_id: str) -> str:
    ids = re.findall(r'\b\d{7,10}\b', user_query, flags=re.IGNORECASE)
    if ids:
        set_last_order_id(user_id, ids[0])
        return f"{user_query}\n\n[CTX] Use ORDER_ID={ids[0]} if needed."
    ctx = get_last_order_id(user_id)
    if ctx:
        return f"{user_query}\n\n[CTX] If the user refers to 'this order' without an ID, assume ORDER_ID={ctx}."
    return user_query

def clean_agent_response(response: str) -> str:
    """Clean agent response to remove unnecessary parts"""
    # Remove common agent artifacts
    response = response.replace("Tool output:", "").strip()
    response = response.replace("Final Answer:", "").strip()
    
    # Remove excessive newlines
    import re
    response = re.sub(r'\n+', '\n', response)
    
    return response.strip()


@router.post("/chat_chatbot")
async def chat_with_bot(query: QueryRequest, user_id: str):
    try:
        print("Chatbot request received", query.user_query)

        classification = await classify_intent(query.user_query)
        print(f"Query classified as: {classification}")

        if classification == "chat":
            # Use Groq LLM for simple chat
            prompt = f"""
            You are a friendly support chatbot.

            Respond **only** with the final message to the user.
            Avoid showing thoughts, reasoning, or any action steps.
            Do not include 'Thought:', 'Action:', or '<think>' blocks.

            User: {query.user_query}
            """

            response = await groq_llm.ainvoke(prompt)
            return {
                "response": (
                    response.content if hasattr(response, "content") else str(response)
                )
            }

        # Use Anthropic Agent with tools for tool-related queries
        tracker = ToolUsageTracker(user_id)
        agent = build_agent(user_id, callbacks=[tracker])
        
        # Enhance query to help agent understand context
        enhanced_query = enhance_query_for_agent(query.user_query, user_id)
        
        response = await agent.ainvoke({"input": enhanced_query})

        if isinstance(response, dict) and "output" in response:
            final_output = response["output"]
        elif hasattr(response, "content"):
            final_output = response.content
        else:
            final_output = str(response)

        # Clean the response
        cleaned_response = clean_agent_response(final_output)
        return {"response": cleaned_response}

    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# scp -i "D:\AMG Projects\Chatbot_Advanced\grocify.pem" -r "D:\AMG Projects\Chatbot_Advanced\wheels" ec2-user@ec2-13-233-43-192.ap-south-1.compute.amazonaws.com:~
