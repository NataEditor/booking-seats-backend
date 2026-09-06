import uuid

from models.action import Action
from services.action import ActionService

from core.db import DBSession


async def get_action_or_404(
    action_id: uuid.UUID,
    session: DBSession,
) -> Action:
    """FastAPI зависимость для получения существующей акции."""
    return await ActionService.get_action_or_raise(action_id, session)
