from collections.abc import Mapping

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from exceptions.action import ActionAlreadyExistsError
from exceptions.base import APIError
from exceptions.cafe import (
    ManagerAlreadyAssignedError,
    ManagerNotFoundError,
    ManagerRoleError,
)
from exceptions.common import BadRequestError, EntityNotFoundError, PermissionDeniedError
from exceptions.dish import DishAlreadyExistsError
from exceptions.user import UserAlreadyExistsError, UserNotFoundError
from schemas.error import CustomError


def custom_error_response(
    status_code: int,
    message: str,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    """Возвращает ошибку в едином формате из спецификации."""
    error = CustomError(code=status_code, message=message)
    return JSONResponse(
        status_code=status_code,
        content=error.model_dump(),
        headers=dict(headers) if headers is not None else None,
    )


_PYDANTIC_ERROR_TRANSLATIONS = {
    'string_type': 'Должно быть строкой',
    'int_type': 'Должно быть целым числом',
    'int_parsing': 'Должно быть целым числом',
    'float_type': 'Должно быть числом',
    'float_parsing': 'Должно быть числом',
    'decimal_type': 'Должно быть числом',
    'decimal_parsing': 'Должно быть числом',
    'bool_type': 'Должно быть логическим значением',
    'bool_parsing': 'Должно быть логическим значением (true/false)',
    'list_type': 'Должен быть списком',
    'uuid_type': 'Должен быть валидным UUID',
    'uuid_parsing': 'Должен быть валидным UUID',
    'date_type': 'Должна быть валидной датой (ГГГГ-ММ-ДД)',
    'time_type': 'Должно быть валидным временем (ЧЧ:ММ:СС)',
    'datetime_type': 'Должно быть валидной датой-временем',
    'finite_number': 'Должно быть конечным числом (NaN/Infinity недопустимы)',
    'missing': 'Обязательное поле отсутствует',
    'string_too_long': 'Строка слишком длинная',
    'string_too_short': 'Строка слишком короткая',
    'less_than_equal': 'Должно быть меньше или равно',
    'greater_than_equal': 'Должно быть больше или равно',
    'less_than': 'Должно быть меньше',
    'greater_than': 'Должно быть больше',
    'json_invalid': 'Некорректный JSON в теле запроса',
    'json_type': 'Некорректный JSON в теле запроса',
    'extra_forbidden': 'Обнаружены лишние поля',
    'literal_error': 'Недопустимое значение',
    'enum': 'Недопустимое значение',
    'value_error': 'Некорректное значение',
}


def _translate_pydantic_error(error: dict) -> str:
    """Переводит типовую ошибку pydantic на русский, иначе — исходный текст."""
    error_type = error.get('type', '')
    if error_type == 'value_error':
        # У value_error в ctx может быть заданное русское сообщение (валидатор)
        ctx = error.get('ctx') or {}
        return str(ctx.get('error', 'Некорректное значение'))
    return _PYDANTIC_ERROR_TRANSLATIONS.get(error_type, error.get('msg', ''))


def _validation_error_message(exception: RequestValidationError) -> str:
    """Собирает ошибки валидации в одно понятное сообщение на русском."""
    messages = []
    for error in exception.errors():
        location = '.'.join(str(part) for part in error['loc'] if part != 'body')
        message = _translate_pydantic_error(error)
        messages.append(f'{location}: {message}' if location else message)
    return '; '.join(messages)


async def http_exception_handler(
    _: Request,
    exception: StarletteHTTPException,
) -> JSONResponse:
    """Преобразует стандартные HTTPException в формат CustomError."""
    return custom_error_response(
        exception.status_code,
        str(exception.detail),
        exception.headers,
    )


async def api_error_handler(
    _: Request,
    exception: APIError,
) -> JSONResponse:
    """Возвращает прикладную ошибку в формате CustomError."""
    return custom_error_response(
        exception.status_code,
        exception.message,
        exception.headers,
    )


async def entity_not_found_handler(
    _: Request,
    exception: EntityNotFoundError,
) -> JSONResponse:
    """Преобразует ошибку сервисного слоя в ответ 404."""
    return custom_error_response(
        status.HTTP_404_NOT_FOUND,
        str(exception),
    )


async def permission_denied_handler(
    _: Request,
    exception: PermissionDeniedError,
) -> JSONResponse:
    """Преобразует запрет сервисного слоя в ответ 403."""
    return custom_error_response(
        status.HTTP_403_FORBIDDEN,
        str(exception),
    )


async def request_validation_error_handler(
    _: Request,
    exception: RequestValidationError,
) -> JSONResponse:
    """Преобразует ошибки FastAPI/Pydantic в формат CustomError."""
    return custom_error_response(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        _validation_error_message(exception),
    )


async def user_already_exists_handler(
    _: Request,
    __: UserAlreadyExistsError,
) -> JSONResponse:
    """Возвращает единый ответ при конфликте уникальных полей."""
    return custom_error_response(
        status.HTTP_400_BAD_REQUEST,
        'Пользователь с такими данными уже существует.',
    )


async def dish_already_exists_handler(
    _: Request,
    __: DishAlreadyExistsError,
) -> JSONResponse:
    """Возвращает единый ответ при конфликте уникального имени блюда."""
    return custom_error_response(
        status.HTTP_400_BAD_REQUEST,
        'Блюдо с таким именем уже существует.',
    )


async def action_already_exists_handler(
    _: Request,
    __: ActionAlreadyExistsError,
) -> JSONResponse:
    """Возвращает единый ответ при конфликте описания акции."""
    return custom_error_response(
        status.HTTP_400_BAD_REQUEST,
        'Акция с таким описанием уже существует.',
    )


async def user_not_found_handler(
    _: Request,
    __: UserNotFoundError,
) -> JSONResponse:
    """Возвращает единый ответ, если пользователь не найден."""
    return custom_error_response(
        status.HTTP_404_NOT_FOUND,
        'Пользователь не найден.',
    )


async def manager_not_found_handler(
    _: Request,
    exception: ManagerNotFoundError,
) -> JSONResponse:
    """Возвращает ошибку, если менеджер не найден."""
    return custom_error_response(
        status.HTTP_404_NOT_FOUND,
        str(exception),
    )


async def manager_role_error_handler(
    _: Request,
    exception: ManagerRoleError,
) -> JSONResponse:
    """Возвращает ошибку, если пользователь не является менеджером."""
    return custom_error_response(
        status.HTTP_400_BAD_REQUEST,
        str(exception),
    )


async def manager_already_assigned_handler(
    _: Request,
    exception: ManagerAlreadyAssignedError,
) -> JSONResponse:
    """Возвращает ошибку, если менеджер уже привязан к другому кафе."""
    return custom_error_response(
        status.HTTP_400_BAD_REQUEST,
        str(exception),
    )


async def duplicate_error_handler(
    request: Request,
    exception: BadRequestError,
) -> JSONResponse:
    """Возвращает ошибку, если объект с одним из уникальных полей уже существует."""
    return custom_error_response(
        status.HTTP_400_BAD_REQUEST,
        str(exception),
    )
