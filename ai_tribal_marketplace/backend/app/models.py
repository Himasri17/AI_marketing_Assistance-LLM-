from sqlalchemy import Column, Integer, String
from .database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    english = Column(String)
    hindi = Column(String)
    marathi = Column(String)
    bengali = Column(String)
    tamil = Column(String)
    telugu = Column(String)

    def __init__(self, english, hindi, marathi, bengali, tamil, telugu):
        self.english = english
        self.hindi = hindi
        self.marathi = marathi
        self.bengali = bengali
        self.tamil = tamil
        self.telugu = telugu
