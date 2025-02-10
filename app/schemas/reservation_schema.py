from pydantic import BaseModel, EmailStr


class Customer(BaseModel):
    name: str
    email: EmailStr
    city: str

class Designer(BaseModel):
    name: str
    salon: str

class ReservationDetails(BaseModel):
    date: str
    time: str
    type: str
    price: int

class Payment(BaseModel):
    method: str
    status: str

class Reservation(BaseModel):
    customer: Customer
    designer: Designer
    reservation: ReservationDetails
    payment: Payment

class ReservationQuery(BaseModel):
    email: EmailStr