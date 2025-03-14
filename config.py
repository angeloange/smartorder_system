import os

class Config:
    # AWS RDS MySQL 設定
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://user1:cAG2x14H6Pw74qW2#73FdhG1A4f#IRfaT1TFE1F2@my-database.cx2cm6iks409.ap-northeast-1.rds.amazonaws.com/beverage_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False