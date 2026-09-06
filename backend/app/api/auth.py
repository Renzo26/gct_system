from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session
from app.models.user import User
from app.schemas.auth import (
    LoginIn,
    RefreshIn,
    SelectWorkshopIn,
    TokenOut,
    UserOut,
    WorkshopListItemOut,
    WorkshopOut,
)
from app.services.auth_service import (
    AuthError,
    ForbiddenError,
    auth_service,
    create_access_token,
    create_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _build_token_out(user: User, workshop=None) -> TokenOut:
    workshop_id = workshop.id if workshop else None
    return TokenOut(
        access_token=create_access_token(user, workshop_id),
        refresh_token=create_refresh_token(user, workshop_id),
        user=UserOut.model_validate(user),
        workshop=WorkshopOut.model_validate(workshop) if workshop else None,
    )


@router.post("/login", response_model=TokenOut)
async def login(body: LoginIn, db: AsyncSession = Depends(get_session)):
    try:
        user = await auth_service.login(db, body.email, body.password)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    # Quem só tem um cliente já entra direto nele; o resto passa pela seleção.
    workshops = await auth_service.list_accessible_workshops(db, user)
    workshop = workshops[0] if len(workshops) == 1 else None
    return _build_token_out(user, workshop)


@router.post("/refresh", response_model=TokenOut)
async def refresh(body: RefreshIn, db: AsyncSession = Depends(get_session)):
    try:
        user, workshop_id = await auth_service.refresh(db, body.refresh_token)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    workshop = None
    if workshop_id is not None:
        workshop = await auth_service.select_workshop(db, user, workshop_id)
    return _build_token_out(user, workshop)


@router.get("/workshops", response_model=list[WorkshopListItemOut])
async def list_my_workshops(
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    return await auth_service.list_accessible_workshops(db, user)


@router.post("/select-workshop", response_model=TokenOut)
async def select_workshop(
    body: SelectWorkshopIn,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    try:
        workshop = await auth_service.select_workshop(db, user, body.workshop_id)
    except ForbiddenError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return _build_token_out(user, workshop)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)
