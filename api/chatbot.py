from fastapi import APIRouter, HTTPException
from models.query_model import QueryRequest
from core.llm import groq_llm
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
    order_not_found,
)
from langchain.agents import initialize_agent, AgentType

router = APIRouter()

# Initialize LangChain agent with tools
tools = [
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
    order_not_found,
]
prefix = """You are an intelligent assistant. If the user's query can be answered by your knowledge or tools, do so.
If the request seems too complex, ambiguous, or requires human empathy and judgment,
use the 'escalate_to_human' tool instead.
"""
agent = initialize_agent(
    tools=tools,
    llm=groq_llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)


@router.post("/chat_chatbot")
async def chat_with_bot(query: QueryRequest):
    try:
        response = agent.run(query.user_query)
        if response.startswith("Order not found."):
            return {"response": response}
        else:
            return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# scp -i "D:\AMG Projects\Chatbot_Advanced\grocify.pem" -r "D:\AMG Projects\Chatbot_Advanced\wheels" ec2-user@ec2-13-233-43-192.ap-south-1.compute.amazonaws.com:~
