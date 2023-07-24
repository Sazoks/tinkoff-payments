from enum import Enum


class TinkoffRoutes(str, Enum):
    """Открытое API платежей Тинькофф"""

    INIT = '/v2/Init/'
    GET_QR = '/v2/GetQr/'
    CANCEL = '/v2/Cancel'
    CONFIRM = '/v2/Confirm'
    SBP_PAY_TEST = '/v2/SbpPayTest'
