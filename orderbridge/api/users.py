import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from orderbridge.adapters.database.repositories import DBUserRepo
from orderbridge.api.dependencies import get_db
from orderbridge.common.types import UserCreate, UserEntity

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/users", status_code=201, response_model=UserEntity)
def create_user(user: UserCreate, db: Session = Depends(get_db)) -> UserEntity:
    try:
        repo = DBUserRepo(db)
        created = repo.insert(user)
        db.commit()
        return created
    except Exception:
        logger.exception("Error creating user")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while creating the user",
        )
