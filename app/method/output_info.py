import threading
from typing import Optional

class OutInfo:
    def __init__(self,data_result: Optional[list]):
        self.DataResult = data_result

    #возвращает информацию об ответе
    async def ReturnedInfo(self):
        if self.DataResult is None:
            return None
        return None


    # возвращает статусы об ответе
    @staticmethod
    async def ReturnedStatus(status: None):
        return status