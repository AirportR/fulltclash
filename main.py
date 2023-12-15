import asyncio
from utils.websocket.ws_server import main


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Websocket server shutting down...")
