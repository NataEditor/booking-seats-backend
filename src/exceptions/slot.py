from fastapi import status

from exceptions.base import APIError


class SlotOverlapError(APIError):
    """Попытка создать слот, пересекающийся по времени с существующим."""

    def __init__(self) -> None:
        """Инициализирует ошибку пересечения слотов."""
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message='Слот пересекается по времени с существующим слотом кафе.',
        )


class SlotTimeRangeError(APIError):
    """Время начала слота не меньше времени окончания."""

    def __init__(self) -> None:
        """Инициализирует ошибку некорректного диапазона времени слота."""
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            message='Время начала должно быть меньше времени окончания',
        )
