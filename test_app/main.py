from typing import Annotated, Union

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel


security = HTTPBasic()
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


class ItemDeleteResponse(BaseModel):
    message: str


class User(BaseModel):
    username: str
    full_name: str
    email: str
    user_id: int


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


@app.delete("/items/{item_id}")
def delete_item(item_id: int) -> ItemDeleteResponse:
    return ItemDeleteResponse(message=f"Item {item_id} deleted successfully")


@app.get("/user/{userid}")
def get_user(credentials: Annotated[HTTPBasicCredentials, Depends(security)], userid: int) -> User:
    if credentials.username == "joulu" and credentials.password == "pukki":
        return User(
            username=credentials.username,
            full_name=f"Joulu Pukki",
            email="joulu.pukki@korvatuntiri.fi",
            user_id=userid,
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Basic"},
    )
