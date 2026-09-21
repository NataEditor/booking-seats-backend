import os
import sys
from pathlib import Path
from unittest import TestCase

from pydantic import ValidationError

os.environ.setdefault('POSTGRES_USER', 'test')
os.environ.setdefault('POSTGRES_PASSWORD', 'test')
os.environ.setdefault('POSTGRES_DB', 'test')
os.environ.setdefault('JWT_SECRET', '01234567890123456789012345678901')
os.environ.setdefault('REDIS_PASSWORD', 'test')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

from schemas.action import ActionCreate  # noqa: E402
from schemas.booking import BookingCreate  # noqa: E402
from schemas.cafe import CafeCreate, CafeUpdate  # noqa: E402
from schemas.dish import DishCreate, DishUpdate  # noqa: E402
from schemas.slots import TimeSlotCreate, TimeSlotUpdate  # noqa: E402
from schemas.table import TableCreate, TableUpdate  # noqa: E402

UUID = '11111111-1111-1111-1111-111111111111'


class SchemaNullNanTests(TestCase):
    """Проверяет приём null/NaN в схемах проекта."""

    def test_cafe_create_rejects_null_name(self) -> None:
        """Обязательное поле name отклоняет null."""
        with self.assertRaises(ValidationError):
            CafeCreate(name=None, address='A', phone='+79991112233', managers_id=[UUID])

    def test_cafe_create_rejects_empty_name(self) -> None:
        """Пустая строка в name отклоняется."""
        with self.assertRaises(ValidationError):
            CafeCreate(name='  ', address='A', phone='+79991112233', managers_id=[UUID])

    def test_cafe_update_rejects_null_name(self) -> None:
        """Upddate не даёт занулить обязательное поле."""
        with self.assertRaises(ValidationError):
            CafeUpdate(name=None)

    def test_table_create_rejects_zero_seats(self) -> None:
        """seat_number должен быть больше нуля."""
        with self.assertRaises(ValidationError):
            TableCreate(seat_number=0)

    def test_slot_create_rejects_null_time(self) -> None:
        """start_time/end_time отклоняют null."""
        with self.assertRaises(ValidationError):
            TimeSlotCreate(start_time=None, end_time='12:00')
        with self.assertRaises(ValidationError):
            TimeSlotCreate(start_time='10:00', end_time=None)

    def test_slot_update_rejects_null_time(self) -> None:
        """PATCH-схема отклоняет явный null в start_time/end_time (422, а не 500)."""
        with self.assertRaises(ValidationError):
            TimeSlotUpdate(start_time=None)
        with self.assertRaises(ValidationError):
            TimeSlotUpdate(end_time=None)
        with self.assertRaises(ValidationError):
            TimeSlotUpdate(is_active=None)

    def test_slot_update_allows_omitted_fields(self) -> None:
        """PATCH-схема принимает частичное обновление без переданных полей."""
        update = TimeSlotUpdate(description='Новое описание')
        self.assertIsNone(update.start_time)
        self.assertIsNone(update.end_time)
    def test_dish_create_rejects_null_name(self) -> None:
        """Обязательное name отклоняет null."""
        with self.assertRaises(ValidationError):
            DishCreate(name=None, price='1.00', cafes_id=[UUID])

    def test_dish_update_rejects_nan_price(self) -> None:
        """NaN в price отклоняется как не-число."""
        with self.assertRaises(ValidationError):
            DishUpdate(price=float('nan'))

    def test_action_create_rejects_empty_cafes(self) -> None:
        """Пустой список cafes_id отклоняется."""
        with self.assertRaises(ValidationError):
            ActionCreate(description='desc', photo_id=None, cafes_id=[])

    def test_table_create_rejects_nan_seats(self) -> None:
        """NaN в seat_number отклоняется как не-число."""
        with self.assertRaises(ValidationError):
            TableCreate(seat_number=float('nan'))

    def test_table_update_rejects_nan_seats(self) -> None:
        """PATCH не даёт записать NaN в seat_number."""
        with self.assertRaises(ValidationError):
            TableUpdate(seat_number=float('nan'))

    def test_dish_create_rejects_null_price(self) -> None:
        """Обязательное price отклоняет null (decimal_type)."""
        with self.assertRaises(ValidationError):
            DishCreate(name='dish', price=None, cafes_id=[UUID])

    def test_dish_create_rejects_nan_price(self) -> None:
        """NaN в price отклоняется как не-число."""
        with self.assertRaises(ValidationError):
            DishCreate(name='dish', price=float('nan'), cafes_id=[UUID])

    def test_dish_create_rejects_non_numeric_price_string(self) -> None:
        """Строка-мусор в price отклоняется (не парсится в Decimal)."""
        with self.assertRaises(ValidationError):
            DishCreate(name='dish', price='abc', cafes_id=[UUID])

    def test_booking_create_rejects_nan_guest_number(self) -> None:
        """NaN в guest_number отклоняется как не-число."""
        with self.assertRaises(ValidationError):
            BookingCreate(
                guest_number=float('nan'),
                booking_date='2026-10-01',
                cafe_id=UUID,
                tables_slots=[],
            )

    def test_booking_create_rejects_zero_reminder(self) -> None:
        """reminder_minutes_before должен быть положительным, 0 отклоняется."""
        with self.assertRaises(ValidationError):
            BookingCreate(
                guest_number=2,
                reminder_minutes_before=0,
                booking_date='2026-10-01',
                cafe_id=UUID,
                tables_slots=[],
            )
