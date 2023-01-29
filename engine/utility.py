from datetime import datetime
from random import randint
from time import sleep
from Crypto.Hash import keccak
from pycoingecko import CoinGeckoAPI

from application_data import app, db
from config import PROCESSING_TIME_IN_SECONDS, CURRENCY_NAME_TO_ACCOUNT_FIELD_MAP, CURRENCY_NAMES_TO_ACCOUNT_BALANCE_MAP
from engine.models.user import User
from models.account import Account
from models.transaction import Transaction


def hash_text(text: str) -> str:
    """
    Hashes text using the keccak 256 algorithm
    :param text: Text that's going to be hashed
    :return: Hashed string
    """
    a_byte_array = bytearray(text, "utf8")
    hashed_text = keccak.new(digest_bits=256)
    hashed_text.update(a_byte_array)
    return hashed_text.hexdigest()


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


def generate_transaction_id(transaction: Transaction) -> None:
    transaction.id = get_hashed_transaction_id(transaction.sender, transaction.receiver, transaction.amount)


def get_crypto_prices():
    """
    Gets crypto prices from the CoinGeckoAPI api
    :return: E.g. [{'cardano': {'usd': 0.31708}, 'bitcoin': {'usd': 16974.59}, 'binancecoin': {'usd': 288.21},
                    'matic-network': {'usd': 0.90794}, 'dogecoin': {'usd': 0.100344}, 'polkadot': {'usd': 5.45},
                    'ethereum': {'usd': 1255.73}}]
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


def process_transactions() -> None:
    """
    Processes all transactions in the state of 'Processing'.
    After 5 minutes have passed since the initial event of the transaction,
    it changes the state of the transaction to 'Processed'.
    :return: None
    """
    with app.app_context():
        while True:
            try:
                sleep(3)  # delay making db query

                # fetch all processing transactions
                processing_transactions = Transaction.query.filter_by(state='Processing').all()
                made_changes: bool = False

                # check if any transactions have been processed and update states if they have
                for transaction in processing_transactions:
                    transaction_date = datetime.strptime(transaction.date, '%Y-%m-%d %H:%M:%S.%f')
                    present_date = datetime.now()

                    difference = present_date - transaction_date
                    diff = difference.total_seconds()

                    if diff >= PROCESSING_TIME_IN_SECONDS:
                        is_valid = perform_transaction(transaction)
                        if is_valid:
                            transaction.state = 'Valid'
                        else:
                            transaction.state = 'Invalid'
                        made_changes = True

                # save changes if any were made
                if made_changes:
                    db.session.commit()
            except:  # NOQA
                pass


def perform_transaction(transaction: Transaction) -> bool:
    try:
        sender_user = User.query.filter_by(email=transaction.sender).first()
        sender_account = Account.query.filter_by(user_id=sender_user.user_id).first()
        receiver_user = User.query.filter_by(email=transaction.receiver).first()
        receiver_account = Account.query.filter_by(user_id=receiver_user.user_id).first()

        currency_attr = CURRENCY_NAMES_TO_ACCOUNT_BALANCE_MAP[transaction.currency]

        if sender_account.__getattribute__(currency_attr) < transaction.amount:
            return False  # Insufficient funds!

        if currency_attr != 'usd_balance' and not receiver_account.__getattribute__(f'{currency_attr[:3]}_enabled'):
            return False  # Recipient doesn't have that currency active!

        # equalize funds
        sender_account.__setattr__(currency_attr, sender_account.__getattribute__(currency_attr) - transaction.amount)
        receiver_account.__setattr__(currency_attr,
                                     receiver_account.__getattribute__(currency_attr) + transaction.amount)
    except:  # NOQA
        return False  # Error occured

    return True
