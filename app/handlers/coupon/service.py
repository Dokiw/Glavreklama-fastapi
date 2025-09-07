import hashlib
from typing import Optional, List
import time
from datetime import datetime, timedelta, UTC

from app.handlers.auth.interfaces import AsyncRoleService
from app.handlers.coupon.interfaces import AsyncCouponService
from app.handlers.coupon.UOW import SqlAlchemyUnitOfWork
from app.handlers.coupon.schemas import CreateCoupon, OutCoupon, CreateCouponService
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from app.core.abs.unit_of_work import IUnitOfWorkCoupon
from app.handlers.session.dependencies import SessionServiceDep
from app.handlers.session.schemas import CheckSessionAccessToken
from app.method.generator_promo import PromoGenerator


class SqlAlchemyCoupon(AsyncCouponService):
    def __init__(self, uow: IUnitOfWorkCoupon, role_service: AsyncRoleService, session_service: SessionServiceDep):
        self.uow = uow
        self.session_service = session_service
        self.role_service = role_service

    async def create_coupon(self, coupon_data: CreateCouponService, check_data: CheckSessionAccessToken) -> Optional[
                                                                                                                OutCoupon] | datetime:
        try:
            async with self.uow:

                await self.session_service.validate_access_token_session(check_data)

                valid = await self.uow.coupon_repo.get_by_user_id(user_id=coupon_data.user_id)

                if valid and valid[0].created_at > (datetime.now(UTC) - timedelta(weeks=1)):
                    return valid[0].created_at

                gen = PromoGenerator()
                res = await gen.generate()

                is_fixed = res['type'] == "fixed"

                init_data = CreateCoupon(
                    user_id=coupon_data.user_id,
                    name=coupon_data.name,
                    description=str(res['value']),
                    promo_count=is_fixed,
                    status=True,
                    token_hash=res['code'],
                )

                result: Optional[OutCoupon] = await self.uow.coupon_repo.create_coupon(
                    init_data
                )
                if result is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Данные не прошли создания"
                    )
                return result
        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            # Откатываем транзакцию при любой другой ошибке
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )

    async def used_coupon(self, token: str, check_data: CheckSessionAccessToken) -> Optional[OutCoupon]:
        try:
            async with self.uow:
                await self.session_service.validate_access_token_session(check_data)

                result: Optional[OutCoupon] = await self.uow.coupon_repo.used_coupon(check_data.user_id, token)

                await self.uow.commit()
                return result
        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            # Откатываем транзакцию при любой другой ошибке
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )

    async def used_any_coupon(self, user_id: int, token: str, check_data: CheckSessionAccessToken) -> Optional[OutCoupon]:
        try:
            async with self.uow:
                await self.role_service.is_admin(check_data.user_id)
                await self.session_service.validate_access_token_session(check_data)

                result: Optional[OutCoupon] = await self.uow.coupon_repo.used_coupon(user_id, token)

                return result
        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            # Откатываем транзакцию при любой другой ошибке
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )

    async def get_by_any_user_id(self, id_user: int, check_data: CheckSessionAccessToken) -> Optional[List[OutCoupon]]:
        try:
            async with self.uow:
                u_r = await self.role_service.is_admin(check_data.user_id)
                if not u_r:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="нет прав"
                    )

                await self.session_service.validate_access_token_session(check_data)
                results: Optional[List[OutCoupon]] = await self.uow.coupon_repo.get_by_user_id(id_user)
                if results is None:
                    return None
                return results
        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            # Откатываем транзакцию при любой другой ошибке
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )

    async def get_by_user_id(self, check_data: CheckSessionAccessToken) -> Optional[List[OutCoupon]]:
        try:
            async with self.uow:
                await self.session_service.validate_access_token_session(check_data)
                results: Optional[List[OutCoupon]] = await self.uow.coupon_repo.get_by_user_id(check_data.user_id)
                if results is None:
                    return None
                return results

        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            # Откатываем транзакцию при любой другой ошибке
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )

    async def get_info_by_coupon_id(self, id: int, check_data: CheckSessionAccessToken) -> Optional[OutCoupon]:
        try:
            async with self.uow:
                await self.session_service.validate_access_token_session(check_data)

                result: Optional[OutCoupon] = await self.uow.coupon_repo.get_info_by_coupon_id(id)

                return result
        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            # Откатываем транзакцию при любой другой ошибке
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )

    async def get_by_token_hash(self, token: str, check_data: CheckSessionAccessToken) -> Optional[OutCoupon]:
        try:
            async with self.uow:
                await self.session_service.validate_access_token_session(check_data)
                result: Optional[OutCoupon] = await self.uow.coupon_repo.get_by_token_hash(token)

                return result
        except HTTPException:
            # просто пробрасываем дальше, чтобы не превращать в 500
            raise
        except Exception as e:
            # Откатываем транзакцию при любой другой ошибке
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Внутренняя ошибка сервера: {str(e)}"
            )
