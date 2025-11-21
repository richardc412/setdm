"""WebSocket routes for realtime message delivery."""
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services import realtime

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/messages")
async def messages_socket(websocket: WebSocket):
    """Stream message events to connected clients."""
    await realtime.manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive; future versions can act on incoming events.
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected by client")
    except Exception as exc:
        logger.error("WebSocket error: %s", exc)
    finally:
        await realtime.manager.disconnect(websocket)


