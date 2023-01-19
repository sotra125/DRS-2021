from pycoingecko import CoinGeckoAPI
from Crypto.Hash import keccak


def hash_text(text):
    byte_array = bytearray(text, "utf8")
    keccak_obj = keccak.new(digest_bits=256)
    keccak_obj.update(byte_array)
    hashed_text = keccak_obj.hexdigest()
    return hashed_text


def get_crypto_prices():
    """
    Fetches crypto market values using the CoinGecko api
    """

    # fetch price data
    cg = CoinGeckoAPI()
    return cg.get_price(ids=['bitcoin', 'ethereum', 'binancecoin', 'matic-network', 'dogecoin', 'cardano', 'polkadot'],
                        vs_currencies='usd')
