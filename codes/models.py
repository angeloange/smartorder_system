from pydantic import BaseModel

class DBUser(BaseModel):
    host: str
    port: int
    user: str
    password: str
    database: str
