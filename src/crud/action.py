import uuid

from loguru import logger
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from crud.base import CRUDBase
from exceptions.action import (
    ActionAlreadyExistsError,
    CafeActionAlreadyExistsError,
    PhotoError,
)
from models.action import Action
from models.cafe import Cafe
from schemas.action import ActionCreate, ActionInfo, ActionUpdate


class ActionCRUD(CRUDBase[Action, ActionCreate, ActionUpdate]):
    """CRUD операции для акций."""

    def __init__(self) -> None:
        """Настраивает модель акции и связь с кафе."""
        super().__init__(Action, ActionInfo, rel_map={'cafes_id': 'cafes'})

    def _translate_integrity_error(self, error: IntegrityError) -> None:
        """Переводит конфликты БД акции в понятные доменные исключения."""
        driver_error = error.orig
        constraint = getattr(driver_error, 'constraint_name', None)
        if constraint == 'actions_description_key':
            raise ActionAlreadyExistsError from error
        if constraint == 'uq_cafe_action':
            raise CafeActionAlreadyExistsError from error
        if constraint == 'fk_action_photo':
            raise PhotoError from error
        super()._translate_integrity_error(error)

    async def get(        self,
        obj_id: uuid.UUID,
        session: AsyncSession,
    ) -> Action | None:
        """Возвращает акцию вместе со связанными кафе."""
        logger.info('Получение акции по ID: {}', obj_id)
        return await super().get(
            obj_id,
            session,
            options=[selectinload(Action.cafes)],
        )

    async def get_all(
        self,
        session: AsyncSession,
        is_active: bool | None = None,
        cafe_id: uuid.UUID | None = None,
    ) -> list[Action]:
        """Возвращает акции с фильтрацией по активности и кафе."""
        logger.info('Получение всех акций: is_active={}, cafe_id={}', is_active, cafe_id)
        query = select(Action)
        if is_active is not None:
            query = query.where(Action.is_active == is_active)
        if cafe_id is not None:
            query = query.join(Action.cafes).where(Cafe.id == cafe_id)
        query = query.options(selectinload(Action.cafes))
        result = await session.execute(query)
        actions = result.scalars().all()
        logger.info('Найдено {} акций', len(actions))
        return actions


action_crud = ActionCRUD()
