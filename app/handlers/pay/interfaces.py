from typing import Protocol, List, Optional, Dict, Any

from app.handlers.pay.schemas import CreatePaymentsOut, PaymentsOut, CreatePaymentsService, UpdatePayments, \
    CreateWallets, \
    UpdateWalletsService, OutWallets, UpdateWallets, CreatePayments
from app.handlers.session.schemas import CheckSessionAccessToken
from task_celery.pay_task.schemas import SubtractionUpdate, SubtractionBase, SubtractionRead, SubtractionList, \
    SubtractionCreate


class AsyncSubtractionRepository(Protocol):

    async def create_subtraction_user(self, create_data: SubtractionCreate) -> SubtractionRead:
        ...

    async def get_subtraction_by_id(self, id: str) -> Optional[SubtractionRead]:
        ...

    async def get_subtraction_user_by_id(self, user_id: int) -> Optional[SubtractionRead]:
        ...

    async def get_subtractions(self, limit: int = 50, offset: int = 0) -> List[SubtractionRead]:
        ...

    async def get_subtractions_count_internal(self) -> int:
        ...

    async def get_subtractions_count(self) -> int:
        ...

    async def update_subtraction_user(self, update_data: SubtractionUpdate) -> SubtractionRead:
        ...

    async def get_subtractions_internal(self, limit: int = 50, offset: int = 0) -> List[SubtractionRead]:
        ...


class AsyncWalletRepository(Protocol):

    async def create_wallet_user(self, create_data: CreateWallets) -> OutWallets:
        ...

    async def update_wallets_user(self, update_data: UpdateWallets) -> OutWallets:
        ...

    # todo - определить в будущем для составления таблицы для bot.
    # async def get_wallet_users(self):
    #    ...

    async def get_wallet_by_id(self, id: int) -> Optional[OutWallets]:
        ...

    async def get_wallet_by_user_id(self, user_id: int) -> Optional[OutWallets]:
        ...


class AsyncPaymentRepository(Protocol):

    async def create_payments(self, create_data: CreatePayments) -> CreatePaymentsOut:
        ...

    async def update_payments(self, update_data: UpdatePayments) -> PaymentsOut:
        ...

    async def get_payments_by_user_id(self, user_id: int) -> Optional[List[PaymentsOut]]:
        ...

    async def get_payments_by_id(self, payments_id: str) -> Optional[PaymentsOut]:
        ...

    async def get_payments_by_idempotency_id(self, idempotency_id: str) -> Optional[PaymentsOut]:
        ...

    async def get_payments_by_user_id_last(self, user_id: int) -> Optional[PaymentsOut]:
        ...


class AsyncWalletService(Protocol):
    async def create_wallet_or_get_wallet(self, check_data: CheckSessionAccessToken) -> OutWallets:
        ...

    async def update_wallets_user(self, update_data: UpdateWalletsService,
                                  check_data: CheckSessionAccessToken) -> OutWallets:
        ...

    async def get_wallet_by_id(self, id: int, check_data: CheckSessionAccessToken) -> Optional[OutWallets]:
        ...

    async def get_wallet_by_user_id_internal(self, id: int) -> Optional[OutWallets]:
        ...

    async def update_wallets_user_internal(self, update_data: UpdateWalletsService) -> OutWallets:
        ...


class AsyncPaymentService(Protocol):

    async def create_payments(self, create_data: CreatePaymentsService,
                              check_data: CheckSessionAccessToken) -> (
            CreatePaymentsOut | PaymentsOut):
        ...

    async def update_payments(self, update_data: UpdatePayments, check_data: CheckSessionAccessToken) -> PaymentsOut:
        ...

    async def get_payments_by_user_id(self, check_data: CheckSessionAccessToken) -> Optional[List[PaymentsOut]]:
        ...

    async def get_payments_by_id(self, payments_id: str, check_data: CheckSessionAccessToken) -> Optional[PaymentsOut]:
        ...

    async def get_payments_by_idempotency_id(self, idempotency_id: str, check_data: CheckSessionAccessToken) -> \
            Optional[PaymentsOut]:
        ...

    async def webhook_pay(self):
        ...


class AsyncApiPaymentService(Protocol):

    async def find_by_local_payment_id(self, local_payment_id: str, page_limit: int = 50) -> Optional[Dict[str, Any]]:
        ...

    async def get_payments_by_idemp(self, idemp: str) -> Optional[Any]:
        ...

    async def get_payments(self, created_at) -> List[Dict[str, Any]]:
        ...

    async def create_payment(
            self,
            amount: Any,
            return_url: str,
            description: str,
            user_id: str,
            payment_id: str,
            idemp: Optional[str] = None,
    ) -> Dict[str, Any]:
        ...
