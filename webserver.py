# webserver.py
from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from database import get_db, Car
from datetime import datetime
from pydantic import BaseModel
import asyncio
import threading
import os
from websocket.websocket_server import start_server
from ftp_processor import start_ftp_processor

app = FastAPI()

class CarCreate(BaseModel):
  name: str
  price_mdl: float
  link: str
  kilometrage: Optional[int]
  color: Optional[str]

class CarResponse(BaseModel):
  id: int
  name: str
  price_mdl: float
  link: str
  kilometrage: Optional[int]
  color: Optional[str]
  created_at: datetime
  updated_at: datetime

  class Config:
    from_attributes = True
    
@app.post('/cars', response_model=CarResponse, status_code=200)
def create_car(car: CarCreate, db: Session = Depends(get_db)):
  car = Car(**car.dict())
  db.add(car)
  db.commit()
  db.refresh(car)
  return car

@app.get('/')
def read_root():
  return {'message': 'welcome to the car API'}

@app.get('/cars', response_model=List[CarResponse])
def read_cars(db: Session = Depends(get_db), limit: int = Query(default=10, ge=1), offset: int = Query(default=0, ge=0)):
  cars = db.query(Car).offset(offset).limit(limit).all()
  return cars

@app.get('/cars/{car_id}', response_model=CarResponse)
def read_car(car_id: int, db: Session = Depends(get_db)):
  car = db.query(Car).filter(Car.id == car_id).first()
  if car is None:
    raise HTTPException(status_code=404, detail='Car not found')
  return car

@app.put('/cars/{car_id}', response_model=CarResponse)
def update_car(car_id: int, car: CarCreate, db: Session = Depends(get_db)):
  car_db = db.query(Car).filter(Car.id == car_id).first()
  if car_db is None:
    raise HTTPException(status_code=404, detail='Car not found')
  for key, value in car.dict().items():
    setattr(car_db, key, value)
  car_db.updated_at = datetime.utcnow()
  db.commit()
  db.refresh(car_db)
  return car_db

@app.delete('/cars/{car_id}')
def delete_car(car_id: int, db: Session = Depends(get_db)):
  car = db.query(Car).filter(Car.id == car_id).first()
  if car is None:
    raise HTTPException(status_code=404, detail='Car not found')
  db.delete(car)
  db.commit()
  return {'message': 'Car deleted'}

@app.post('/upload/')
async def upload_file(file: UploadFile = File(...)):
  try:
    if file.content_type != 'application/json':
      raise HTTPException(status_code=400, detail='Only JSON files are allowed')
    content = await file.read()
    try:
      data = json.loads(content)
      print("Received data:", json.dumps(data, indent=2))
      cars = data.get('products_filtered', [])
      db = next(get_db())
      for car in cars:
        car = Car(
          name=car_data.get('name', ''),
          price_mdl=car_data.get('price_mdl', 0.0),
          link=car_data.get('link', ''),
          kilometrage=car_data.get('kilometrage', 0),
          color=car_data.get('color', '')
        )
        db.add(car)
      db.commit()
      return{"message": "File uploaded successfully", "content": data}
    except json.JSONDecodeError:
      raise HTTPException(status_code=400, detail='Invalid JSON file')
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))

WEB_SERVER_NODES = [
  ('localhost', 8001),  # First server
  ('localhost', 8002),  # Second server
  ('localhost', 8003)   # Third server
]

def run_fastapi(host, port):
  import uvicorn
  uvicorn.run(app, host=host, port=port)

async def main():
  current_host = 'localhost'
  current_port = 8001
  
  ftp_thread = start_ftp_processor()
  http_thread = threading.Thread(
    target=run_fastapi,
    args=(current_host, current_port),
    daemon=True
  )
  http_thread.start()
  websocket_task = asyncio.create_task(start_server())
  await websocket_task

if __name__ == '__main__':
  asyncio.run(main())