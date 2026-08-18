import uvicorn
import os

from common.constant import HOST


if __name__ == "__main__":
    internal_port = int(os.getenv("INTERNAL_PORT", "8007"))
    reload = os.getenv("RELOAD", "false").lower() in ("1", "true", "yes")
    reload_dirs = ["./"] if reload else None
    uvicorn.run(
        "api:app",
        host=HOST,
        port=internal_port,
        reload=reload,
        reload_dirs=reload_dirs,
    )
