"""Employee CRUD HTTP endpoints backed by process-local memory."""

from datetime import datetime, timezone
from itertools import count
from threading import Lock
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.schemas import EmployeeCreate, EmployeeResponse, ErrorResponse

router = APIRouter(prefix="/employees", tags=["employees"])
_employees: dict[int, EmployeeResponse] = {}
_next_employee_id = count(1)
_store_lock = Lock()


def reset_employee_store() -> None:
    """Clear process-local state; intended for isolated automated tests."""

    global _next_employee_id
    with _store_lock:
        _employees.clear()
        _next_employee_id = count(1)


@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": ErrorResponse}},
)
def create_employee(payload: EmployeeCreate) -> EmployeeResponse:
    """Create an employee; email addresses must be unique."""

    with _store_lock:
        if any(employee.email == payload.email for employee in _employees.values()):
            raise HTTPException(
                status_code=409,
                detail="An employee with this email already exists",
            )
        employee = EmployeeResponse(
            id=next(_next_employee_id),
            created_at=datetime.now(timezone.utc),
            **payload.model_dump(),
        )
        _employees[employee.id] = employee
        return employee


@router.get("", response_model=list[EmployeeResponse])
def list_employees(
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[EmployeeResponse]:
    """List employees with bounded offset pagination."""

    with _store_lock:
        employees = sorted(_employees.values(), key=lambda employee: employee.id)
        return employees[offset : offset + limit]


@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_employee(employee_id: int) -> EmployeeResponse:
    """Return one employee or a clear 404 response."""

    with _store_lock:
        employee = _employees.get(employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
def delete_employee(employee_id: int) -> Response:
    """Delete one employee or return 404 when it does not exist."""

    with _store_lock:
        if employee_id not in _employees:
            raise HTTPException(status_code=404, detail="Employee not found")
        del _employees[employee_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)
