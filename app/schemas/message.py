from pydantic import BaseModel

class Msg(BaseModel):
    detail: str

class OrderDeleteResponse(BaseModel):
    id: int
    detail: str = "Order deleted successfully"

