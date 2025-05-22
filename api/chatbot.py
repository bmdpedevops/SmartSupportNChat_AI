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
    get_orders_by_item_names_tool,
    search_products,
    check_order_status,
    get_orders,
)
from langchain.agents import initialize_agent, AgentType, Tool
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


def build_agent(user_id: str, callbacks=None):
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
        Tool(
            name="get_orders",
            func=lambda x: get_orders(user_id),
            description="Get all orders placed by the user with the provided user_id.",
        ),
        Tool(
            name="get_orders_by_item_names",
            func=lambda input: get_orders_by_item_names_tool(
                f'{{"item_names": "{input}", "user_id": "{user_id}"}}'
            ),
            description="Search for orders by item names provided as a comma-separated string (e.g., 'Bread,Butter').",
        ),
        Tool(
            name="search_products",
            func=search_products,
            description="Searches for a product by name and returns its details",
        ),
        check_order_status,
    ]

    prefix = f"""You are an intelligent assistant. If the user's query can be answered by your knowledge or tools, do so.
    If the request seems too complex, ambiguous, or requires human empathy and judgment,
    use the 'escalate_to_human' tool instead. The user ID is {user_id}."""

    return initialize_agent(
        tools=tools,
        llm=groq_llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        agent_kwargs={"prefix": prefix},
        callbacks=callbacks or [],
    )


async def summarize_response(raw_output: str, user_query: str) -> str:
    prompt = f"""
You are a helpful assistant. Summarize the response to the user's query interactively and conversationally.

User query: {user_query}

Raw tool response:
{raw_output}

Be friendly, dynamic, and avoid repeating the exact output. Mention insights like number of orders, favorites,amounts, etc.

format the response in such a way that it should include all the information that the user needs to know.and it should be in a structured way with professional tone.
"""
    response = await groq_llm.ainvoke(prompt)
    print(f"response in summarize_response: {response}")
    return (
        response.content if hasattr(response, "content") else str(response["response"])
    )


@router.post("/chat_chatbot")
async def chat_with_bot(query: QueryRequest, user_id: str):
    try:
        tracker = ToolUsageTracker()
        agent = build_agent(user_id, callbacks=[tracker])
        print(f"agent: {agent}")
        response = await agent.ainvoke({"input": query.user_query})
        print(f"response in chat_with_bot: {response}")

        if tracker.tool_used:
            summarized_response = await summarize_response(
                raw_output=response["output"], user_query=query.user_query
            )
            print(f"summarized_response in tool tracker: {summarized_response}")
            return {"response": summarized_response}
        else:
            print(f"response in tool without tracker: {response}")
            return {"response": response["output"]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# scp -i "D:\AMG Projects\Chatbot_Advanced\grocify.pem" -r "D:\AMG Projects\Chatbot_Advanced\wheels" ec2-user@ec2-13-233-43-192.ap-south-1.compute.amazonaws.com:~
