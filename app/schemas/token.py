from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    # Add other relevant data you might store in the token, like user_id or roles
    # user_id: Optional[int] = None
    # roles: Optional[List[str]] = None

