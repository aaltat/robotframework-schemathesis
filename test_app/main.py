from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
app.title = "Test API"
app.description = "This is a test API"
app.version = "1.0.0"
app.openapi_version = "3.0.4"


class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None


class Root(BaseModel):
    message: str
    version: str = app.version


class ItemResponse(BaseModel):
    item_id: int
    q: Union[str, None] = None


class ItemUpdateResponse(BaseModel):
    item_name: str
    item_id: int
    price: float


@app.get("/")
async def read_root() -> Root:
    return Root(message="Hello World")


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: Union[str, None] = None) -> ItemResponse:
    return ItemResponse(item_id=item_id, q=q)


@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item) -> ItemUpdateResponse:
    return ItemUpdateResponse(
        item_name=item.name,
        item_id=item_id,
        price=item.price,
    )
