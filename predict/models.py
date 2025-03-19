from pydantic import BaseModel

#單日總銷量
class Pred_total(BaseModel):
    date_string: str
    weather: str
    temperature: int
    model_filename: str

#每品項銷量
class Pred_sales(BaseModel):
    date_string: str
    weather: str
    temperature: int
    daily_total_sales: int
    model_filename: str
    csv_filename: str