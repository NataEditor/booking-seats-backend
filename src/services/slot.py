import uuid
from datetime import time

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from crud.slot import slot_crud
from exceptions.slot import SlotOverlapError, SlotTimeRangeError
from models.slots import Slot
from models.user import User
from schemas.slots import TimeSlotCreate, TimeSlotUpdate
from services.cafe import ensure_manager_cafe_access
from services.cafe_resource import get_cafe_resource_or_raise

from core.redis import redis_dep


class SlotService:
    """Сервис для работы с временными слотами."""

    @staticmethod
    async def get_slot_in_cafe_or_raise(
        cafe_id: uuid.UUID,
        slot_id: uuid.UUID,
        session: AsyncSession,
    ) -> Slot:
        """Возвращает слот указанного кафе или сообщает, что он не найден."""
        slot = await get_cafe_resource_or_raise(
            cafe_id,
            slot_id,
            session,
            slot_crud,
            'Слот не найден в этом кафе',
        )
        logger.info('Слот принадлежит кафе: cafe_id={}, slot_id={}', cafe_id, slot_id)
        return slot

    @staticmethod
    async def check_slot_not_overlapping(
        cafe_id: uuid.UUID,
        start_time: time,
        end_time: time,
        session: AsyncSession,
        exclude_slot_id: uuid.UUID | None = None,
    ) -> None:
        """Проверяет, что слот не пересекается по времени с существующими в кафе.

        exclude_slot_id позволяет исключить из проверки сам обновляемый слот,
        чтобы PATCH не конфликтовал с текущими значениями.
        """
        logger.info(
            'Проверка пересечения слота: cafe_id={}, start_time={}, end_time={}, exclude_slot_id={}',
            cafe_id,
            start_time,
            end_time,
            exclude_slot_id,
        )
        query = select(Slot).where(
            Slot.cafe_id == cafe_id,
            Slot.is_active.is_(True),
            Slot.start_time < end_time,
            start_time < Slot.end_time,
        )
        if exclude_slot_id is not None:
            query = query.where(Slot.id != exclude_slot_id)

        existing = await session.execute(query)
        if existing.scalars().first() is not None:
            logger.warning(
                'Обнаружен пересекающийся слот в кафе: cafe_id={}, start_time={}, end_time={}',
                cafe_id,
                start_time,
                end_time,
            )
            raise SlotOverlapError

    @staticmethod
    async def create_slot_in_cafe(
        cafe_id: uuid.UUID,
        slot_create: TimeSlotCreate,
        current_user: User,
        session: AsyncSession,
        redis: redis_dep,
    ) -> Slot:
        """Проверяет доступ менеджера и отсутствие пересечений, затем создаёт слот."""
        ensure_manager_cafe_access(current_user, cafe_id)
        await SlotService.check_slot_not_overlapping(
            cafe_id,
            slot_create.start_time,
            slot_create.end_time,
            session,
        )
        return await slot_crud.create_with_cafe(cafe_id, slot_create, session, redis)

    @staticmethod
    async def update_slot_in_cafe(
        cafe_id: uuid.UUID,
        slot: Slot,
        slot_update: TimeSlotUpdate,
        current_user: User,
        session: AsyncSession,
        redis: redis_dep,
    ) -> Slot:
        """Проверяет доступ менеджера и пересечения, затем обновляет слот.

        При частичном обновлении (передан только start_time или только end_time)
        проверка выполняется по итоговой паре значений: новое значение поля
        подставляется вместо текущего.
        """
        ensure_manager_cafe_access(current_user, cafe_id)

        start_time = slot_update.start_time or slot.start_time
        end_time = slot_update.end_time or slot.end_time

        if start_time >= end_time:
            raise SlotTimeRangeError
        await SlotService.check_slot_not_overlapping(
            cafe_id,
            start_time,
            end_time,
            session,
            exclude_slot_id=slot.id,
        )
        return await slot_crud.update(slot, slot_update, session, redis)
