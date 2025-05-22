from pydantic import BaseModel, HttpUrl
from typing import Optional, List


class QueryRequest(BaseModel):
    user_query: str


class MenuItemResponse(BaseModel):
    item_name: str
    description: Optional[str]
    price: float
    discounted_price: float
    image_url: HttpUrl
    packing_price: Optional[float] = 0.0
    is_veg: bool
    is_out_of_stock: bool
