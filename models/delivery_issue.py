from pydantic import BaseModel


class DeliveryIssue(BaseModel):
    order_id: str
    issue: str
    created_at: str
