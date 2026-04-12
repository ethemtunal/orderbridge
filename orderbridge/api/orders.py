import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from orderbridge.api.dependencies import get_db
from orderbridge.common.types import OrderCreate
from orderbridge.services.order_service import get_order_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/orders", status_code=201)
def create_order(
    order: OrderCreate,
    background_tasks: BackgroundTasks,
    x_user_uuid: str = Header(...),
    db: Session = Depends(get_db),
):
    try:
        service = get_order_service(db)
        db_order = service.create_order(x_user_uuid, order)
        db.commit()
        background_tasks.add_task(service.place_order_with_retry, db_order.uuid)
        return db_order
    except Exception:
        logger.exception("Error creating order")
        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error while placing the order"},
        )
