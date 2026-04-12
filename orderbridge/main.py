import logging

import uvicorn
from fastapi import FastAPI

from orderbridge.api.orders import router as orders_router
from orderbridge.api.users import router as users_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="orderbridge")
app.include_router(orders_router)
app.include_router(users_router)


if __name__ == "__main__":
    uvicorn.run("orderbridge.main:app", host="0.0.0.0", port=8000, reload=True)
