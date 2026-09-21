"""add_indexes_and_check_constraints

Revision ID: f1a2b3c4d5e6
Revises: 199a233798f4
Create Date: 2026-09-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = '199a233798f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Добавляет индексы связей, убирает дубль и вводит проверки целостности."""
    # Композитный index user_booking_date уже покрывает выборку по user_id
    op.drop_index('ix_bookings_user_id', table_name='bookings')

    # Индексы на второй столбец связующих таблиц для выборки «блюда/акции кафе X»
    op.create_index('ix_cafe_dishes_dish_id', 'cafe_dishes', ['dish_id'], unique=False)
    op.create_index('ix_cafe_actions_action_id', 'cafe_actions', ['action_id'], unique=False)

    # Проверки целостности на уровне БД
    op.create_check_constraint('check_table_seat_number_positive', 'tables', 'seat_number > 0')
    op.create_check_constraint('check_booking_guest_number_positive', 'bookings', 'guest_number > 0')
    op.create_check_constraint('check_slot_time_range', 'slots', 'end_time > start_time')


def downgrade() -> None:
    """Откатывает индексы и проверки целостности."""
    op.drop_constraint('check_slot_time_range', 'slots', type_='check')
    op.drop_constraint('check_booking_guest_number_positive', 'bookings', type_='check')
    op.drop_constraint('check_table_seat_number_positive', 'tables', type_='check')

    op.drop_index('ix_cafe_actions_action_id', table_name='cafe_actions')
    op.drop_index('ix_cafe_dishes_dish_id', table_name='cafe_dishes')

    op.create_index('ix_bookings_user_id', 'bookings', ['user_id'], unique=False)
