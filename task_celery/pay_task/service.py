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
from app.core.abs.unit_of_work import IUnitOfWorkWallet, IUnitOfWorkCoupon, IUnitOfWorkSubtraction
from app.handlers.session.dependencies import SessionServiceDep
from app.handlers.session.schemas import CheckSessionAccessToken
from app.method.generator_promo import PromoGenerator
from task_celery.pay_task.interfaces import AsyncSubtractionService


class SqlAlchemySubtractionService(AsyncSubtractionService):
    def __init__(self, uow: IUnitOfWorkSubtraction, ):
        self.uow = uow





