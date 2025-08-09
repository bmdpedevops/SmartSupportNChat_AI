from fastapi import APIRouter, HTTPException
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
    def __init__(self):
        self.tool_used = False

    async def on_tool_start(self, serialized, input_str, **kwargs):
        print(f"Tool started: {serialized.get('name')} with input: {input_str}")
        self.tool_used = True


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
        llm=anthropic_llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        max_iterations=7,
        agent_kwargs={"prefix": prefix},
        callbacks=callbacks or [],
        early_stopping_method="generate",
        handle_parsing_errors=True,
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
    prompt = f"""
You are an intent classifier. Classify this message into EXACTLY one category:

1. "chat" - Greetings, thanks, what can you do, general conversation
2. "tool" - Order status, refund, cancel, delivery issues, order details, any specific action needed

Examples:
- "hi" → chat
- "hello" → chat  
- "thanks" → chat
- "what can you help me with" → chat
- "where is my order" → tool
- "order status for 123456" → tool
- "cancel my order" → tool
- "refund request" → tool
- "my order is late" → tool

User message: "{user_query.strip()}"

Respond with only one word: "chat" or "tool"
"""
    
    response = await groq_llm.ainvoke(prompt)
    result = response.content.strip().lower()
    
    # More specific classification
    chat_keywords = ["hi", "hello", "hey", "thanks", "thank you", "what can you do", "help me", "capabilities"]
    tool_keywords = ["order", "refund", "cancel", "delivery", "status", "track", "issue", "problem"]
    
    if any(keyword in user_query.lower() for keyword in chat_keywords):
        return "chat"
    elif any(keyword in user_query.lower() for keyword in tool_keywords):
        return "tool"
    
    return "tool" if result == "tool" else "chat"


@router.post("/chat_chatbot")
async def chat_with_bot(query: QueryRequest, user_id: str):
    try:
        print("Chatbot request received", query.user_query)

        classification = await classify_intent(query.user_query)
        print(f"Query classified as: {classification}")

        if classification == "chat":
            # Directly use Groq LLM
            prompt = f"""
            You are a friendly support chatbot.

            Respond **only** with the final message to the user.
            Avoid showing thoughts, reasoning, or any action steps.
            Do not include 'Thought:', 'Action:', or '<think>' blocks.

            User: {query.user_query}
            """

            response = await groq_llm.ainvoke(prompt)
            # response = response.split("</think>")
            return {
                "response": (
                    response.content if hasattr(response, "content") else str(response)
                )
            }

        # Else use Anthropic Agent with tools
        tracker = ToolUsageTracker()
        agent = build_agent(user_id, callbacks=[tracker])
        response = await agent.ainvoke({"input": query.user_query})

        if isinstance(response, dict) and "output" in response:
            final_output = response["output"]
        elif hasattr(response, "content"):
            final_output = response.content
        else:
            final_output = str(response)

        # summarized = await summarize_response(final_output, query.user_query)
        return {"response": final_output}

    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# scp -i "D:\AMG Projects\Chatbot_Advanced\grocify.pem" -r "D:\AMG Projects\Chatbot_Advanced\wheels" ec2-user@ec2-13-233-43-192.ap-south-1.compute.amazonaws.com:~
