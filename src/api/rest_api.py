from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional
import uuid
from datetime import datetime

from src.core import llm_router
from src.utils.db import get_db_session, save_interaction_to_db, get_latest_tracking_info
from sqlalchemy import text

api_router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class TrackingRequest(BaseModel):
    tracking_code: str = Field(description="The package tracking code, e.g. PKG123456")


class ProfileUpdateRequest(BaseModel):
    user_id: str = "06cecdbd-ac6b-45f5-84f7-c6a8631a4ed6"
    field_type: str = Field(description="Field to update: address or city")
    field_value: str = Field(description="New value for the field")


class OrderCreateRequest(BaseModel):
    sender_name: str
    sender_address: str
    sender_city: str
    sender_country: str
    sender_phone: str
    recipient_name: str
    recipient_address: str
    recipient_city: str
    recipient_country: str
    recipient_phone: str
    package_weight_kg: float
    package_description: str
    shipping_type: str = "Standard"
    special_instructions: str = ""


@api_router.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        response = llm_router(request.message)
        save_interaction_to_db(question=request.message, response=response)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/api/track")
async def track_package(request: TrackingRequest):
    try:
        result = get_latest_tracking_info(request.tracking_code)
        if result:
            last_update = result["last_update"]
            if hasattr(last_update, "isoformat"):
                last_update = last_update.isoformat()
            return {
                "tracking_code": request.tracking_code,
                "status": result["status"],
                "last_update": last_update,
                "location": result["location"],
                "shipping_type": result["shipping_type"],
            }
        raise HTTPException(status_code=404, detail="Tracking code not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/api/update-profile")
async def update_profile(request: ProfileUpdateRequest):
    try:
        from src.core.update_user_profile import update_user_profile
        result = update_user_profile(
            user_input=f"Update my {request.field_type} to {request.field_value}",
            user_id=request.user_id,
        )
        if result is None:
            raise HTTPException(status_code=400, detail="Failed to update profile")
        return {
            "status": "success",
            "field_type": result.field_type,
            "field_value": result.field_value,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/api/orders")
async def create_order(request: OrderCreateRequest):
    try:
        order_id = str(uuid.uuid4())
        SessionLocal = get_db_session()
        query = text(
            """
            INSERT INTO orders (order_id, sender_name, sender_address, sender_city, sender_country, sender_phone,
                               recipient_name, recipient_address, recipient_city, recipient_country, recipient_phone,
                               package_weight_kg, package_description, shipping_type, special_instructions, order_status, created_at)
            VALUES (:order_id, :sender_name, :sender_address, :sender_city, :sender_country, :sender_phone,
                    :recipient_name, :recipient_address, :recipient_city, :recipient_country, :recipient_phone,
                    :package_weight_kg, :package_description, :shipping_type, :special_instructions, 'Pending', :created_at)
            """
        )
        with SessionLocal() as session:
            session.execute(
                query,
                {
                    "order_id": uuid.UUID(order_id),
                    "sender_name": request.sender_name,
                    "sender_address": request.sender_address,
                    "sender_city": request.sender_city,
                    "sender_country": request.sender_country,
                    "sender_phone": request.sender_phone,
                    "recipient_name": request.recipient_name,
                    "recipient_address": request.recipient_address,
                    "recipient_city": request.recipient_city,
                    "recipient_country": request.recipient_country,
                    "recipient_phone": request.recipient_phone,
                    "package_weight_kg": request.package_weight_kg,
                    "package_description": request.package_description,
                    "shipping_type": request.shipping_type,
                    "special_instructions": request.special_instructions,
                    "created_at": datetime.now(),
                },
            )
            session.commit()
        return {"order_id": order_id, "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
