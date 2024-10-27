from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from database import get_db, Car
from datetime import datetime
from pydantic import BaseModel

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

@app.post('/cars', response_model=CarResponse)
def create_car(car: CarCreate, db: Session = Depends(get_db)):
  car = Car(**car.dict())
  db.add(car)
  db.commit()
  db.refresh(car)
  return car

# with pagination
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

# file upload endpoint
@app.post('/upload/')
async def upload_file(file: UploadFile = File(...)):
  if file.content_type != 'application/json':
    raise HTTPException(status_code=400, detail='Only JSON files are allowed')
  content = await file.read()
  try:
    data = json.loads(content)
    print("Data:", data)
    return{"message": "File uploaded successfully", "content": data}
  except json.JSONDecodeError:
    raise HTTPException(status_code=400, detail='Invalid JSON file')

if __name__ == '__main__':
  import uvicorn
  uvicorn.run(app, host='0.0.0.0', port=8001)