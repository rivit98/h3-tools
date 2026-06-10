import asyncio
from dataclasses import asdict

from executor.account import Account
from common import logger


class AccountPool:

    def __init__(self, config):
        self.accounts = list(map(lambda acc: Account(**asdict(acc)), config.accounts))
        self.free_accounts = asyncio.Queue(len(self.accounts))
        for account in self.accounts:
            self.free_accounts.put_nowait(account)

    async def get_available(self) -> Account:
        logger.info('Requesting account')
        acc = await self.free_accounts.get()
        logger.info(f'Found free account: {acc}')
        return acc

    async def return_back(self, acc: Account):
        logger.info(f'Return back account: {acc}')
        await self.free_accounts.put(acc)

