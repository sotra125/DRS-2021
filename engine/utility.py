from random import randint

from pycoingecko import CoinGeckoAPI
from Crypto.Hash import keccak

from engine.config import CURRENCY_NAME_TO_ACCOUNT_FIELD_MAP
from engine.models.account import Account


def hash_text(text):
    byte_array = bytearray(text, "utf8")
    keccak_obj = keccak.new(digest_bits=256)
    keccak_obj.update(byte_array)
    hashed_text = keccak_obj.hexdigest()
    return hashed_text


def get_hashed_transaction_id(user_1: str, user_2: str = '', amount='') -> str:
    """
    Generate random hash value for transactions
    :param user_1: Email of user (sending user in the case of fund sending)
    :param user_2: Email of receiving user in the case of fund sending
    :param amount: Amount of funds being transferred in the case of a transfer
    :return: Hash string which is meant to be used as the transaction ID
    """
    random_value = randint(1, 100000000000)
    return hash_text(f'{user_1}{user_2}{amount}{random_value}')


def get_crypto_prices():
    """
    Fetches crypto market values using the CoinGecko api
    """

    # fetch price data
    cg = CoinGeckoAPI()
    return cg.get_price(ids=['bitcoin', 'ethereum', 'binancecoin', 'matic-network', 'dogecoin', 'cardano', 'polkadot'],
                        vs_currencies='usd')


def convert(from_currency: str, to_currency: str, amount: float) -> float:
    """
    Converts one currency into another
    :param from_currency: Currency you're converting from, e.g. 'btc_balance'
    :param to_currency: Currency you're converting to, e.g. 'usd_balance'
    :param amount: Amount of the currency you're converting from
    :return: Amount of currency you're converting to you can get for this amount of the currency you're converting from
    """
    currency_map = {
        'btc_balance': 'bitcoin',
        'eth_balance': 'ethereum',
        'bnb_balance': 'binancecoin',
        'pol_balance': 'matic-network',
        'dog_balance': 'dogecoin',
        'ada_balance': 'cardano',
        'dot_balance': 'polkadot'
    }

    prices = get_crypto_prices()
    f_curr_usd_value: float = prices[currency_map[from_currency]]['usd'] if from_currency != 'usd_balance' else 1
    t_curr_usd_value: float = prices[currency_map[to_currency]]['usd'] if to_currency != 'usd_balance' else 1
    return round((f_curr_usd_value / t_curr_usd_value) * amount, 7)


def activate_currency(account: Account, currency: str) -> None:
    """
    Activates currency for account
    :param account: User account
    :param currency: Currency to activate, e.g. 'bitcoin'
    :return: None
    """

    curr_enable = f'{CURRENCY_NAME_TO_ACCOUNT_FIELD_MAP[currency]}_enabled'
    account.__setattr__(curr_enable, True)


def deactivate_currency(account: Account, currency: str) -> bool:
    """
    Disables currency for account and converts all existing funds from that currency to USD.
    :param account: User account
    :param currency: Currency to deactivate, e.g. 'bitcoin'
    :return: True if there were no exceptions thrown in the process, else False
    """

    curr_enable = f'{CURRENCY_NAME_TO_ACCOUNT_FIELD_MAP[currency]}_enabled'
    curr_balance = f'{CURRENCY_NAME_TO_ACCOUNT_FIELD_MAP[currency]}_balance'

    try:
        # if currency is already inactive, nothing to do
        if not account.__getattribute__(curr_enable):
            return True

        amount_in_usd = convert(curr_balance, 'usd_balance', account.__getattribute__(curr_balance))

        # transfer funds from that currency to usd
        account.__setattr__(curr_balance, 0)
        account.__setattr__('usd_balance', float(account.__getattribute__('usd_balance')) + amount_in_usd)

        # disable that currency
        account.__setattr__(curr_enable, False)

        return True
    except:  # NOQA
        return False
