from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:yum3lo@postgres:5432/car_database')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

class Car(Base):
  __tablename__ = 'cars'
  id = Column(Integer, primary_key=True, index=True)
  name = Column(String)
  price_mdl = Column(Float)
  link = Column(String, unique=True)
  kilometrage = Column(Integer)
  color = Column(String)
  created_at = Column(DateTime, default=datetime.utcnow)
  updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def init_db():
  Base.metadata.create_all(bind=engine)

def get_db():
  db = Session()
  try:
    yield db
  finally:
    db.close()

init_db()