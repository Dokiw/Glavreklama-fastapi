from typing import Protocol, List, Optional, Dict, Any

from app.handlers.pay.schemas import CreatePaymentsOut, PaymentsOut, CreatePayments, UpdatePayments, CreateWallets, \
    UpdateWalletsService, OutWallets


class AsyncWalletRepository(Protocol):

    async def create_wallet_user(self, create_data: CreateWallets) -> OutWallets:
        ...

    async def update_wallets_user(self, update_data: UpdateWalletsService) -> OutWallets:
        ...

    # todo - определить в будущем для составления таблицы для bot.
    # async def get_wallet_users(self):
    #    ...

    async def get_wallet_by_id(self, id: int) -> Optional[OutWallets]:
        ...

    async def get_wallet_by_user_id(self, user_id: int) -> Optional[OutWallets]:
        ...


class AsyncPaymentRepository(Protocol):

    async def create_payments(self) -> CreatePaymentsOut:
        ...

    async def update_payments(self) -> PaymentsOut:
        ...

    async def get_payments_by_user_id(self) -> Optional[PaymentsOut]:
        ...

    async def get_payments_by_id(self) -> Optional[PaymentsOut]:
        ...

    async def get_payments_by_idempotency_id(self) -> Optional[PaymentsOut]:
        ...
