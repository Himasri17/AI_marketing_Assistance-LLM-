from pydantic import BaseModel

class ProductResponse(BaseModel):
    english: str
    hindi: str
    maithili: str
    konkani: str