import uuid
import os
import random
from datetime import date
from enum import Enum
from typing import List

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr

from eventsourcing.application.sqlalchemy import SQLAlchemyApplication
from eventsourcing.system.runner import SingleThreadedRunner

from boxsystem import BoxSystem, User, Negotiations

app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Contact(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str

class ShipmentSizes(str, Enum):
    S = 'S'
    M = 'M'
    L = 'L'
    XL = 'XL'

class SendRequest(BaseModel):
    """
    I want to drop you something off
    Sender -> Backend -> Receiver
    """
    #id: uuid.UUID
    sender: uuid.UUID
    receiver: uuid.UUID
    #box: uuid.UUID
    #size: ShipmentSizes
    #dropoff_date: date

@app.post("/requests/new")
async def new_request(send_request: SendRequest):
    """
    This endpoint is used when A wants to send something to B
    :param send_request:
    :return:
    """
    print(f'got send request: {send_request}')

    os.environ["DB_URI"] = "sqlite:///db.sqlite"
    system = BoxSystem(
        infrastructure_class=SQLAlchemyApplication,
        setup_tables=True,
        uri='sqlite:///a.db'
    )

    runner = SingleThreadedRunner(system)

    runner.start()

    users = runner.processes['users']
    shippings = runner.processes['shippings']

    sender: User = users.get_user(send_request.sender)
    receiver: User = users.get_user(send_request.receiver)
    

    sender.start_shipping(receiver.id)

    sender.__save__()

    shipping_id = sender.shippings[0]

    runner.close()

    return "id: " + str(shipping_id)

@app.get('/requests/{user_id}')
async def get_open_requests(user_id: uuid.UUID):
    """
    Fetch all open Requets to given user
    :param user_id:
    :return:
    """
    os.environ["DB_URI"] = "sqlite:///db.sqlite"
    system = BoxSystem(
        infrastructure_class=SQLAlchemyApplication,
        setup_tables=True,
        uri='sqlite:///a.db'
    )

    runner = SingleThreadedRunner(system)

    runner.start()

    users = runner.processes['users']
    shippings = runner.processes['shippings']

    user: User = users.get_user(user_id)
    
    runner.close()
    return user.shippings

@app.get("/debug/user")
def new_debug_user(response_model=Contact):
    os.environ["DB_URI"] = "sqlite:///db.sqlite"
    system = BoxSystem(
        infrastructure_class=SQLAlchemyApplication,
        setup_tables=True,
        uri='sqlite:///a.db'
    )

    runner = SingleThreadedRunner(system)

    runner.start()

    users = runner.processes['users']

    user: User = users.create_user("User" + str(random.randint(0,100)), str(random.randint(0,100)) + "@b.c")

    user.__save__()

    runner.close()

    return Contact(id=user.id, email=user.email, name=user.name)