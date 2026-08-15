import uvicorn
import os
from fastapi import FastAPI
from common.constant import HOST,PORT


if __name__ == "__main__":
    internal_port = int(os.getenv("INTERNAL_PORT", "7861"))
    uvicorn.run("api:app", host=HOST, port=internal_port, reload=False)