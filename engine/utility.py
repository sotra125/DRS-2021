from pycoingecko import CoinGeckoAPI


def get_crypto_prices():
    """
    Fetches crypto market values using the CoinGecko api
    """

    # fetch price data
    cg = CoinGeckoAPI()
    return cg.get_price(ids=['bitcoin', 'ethereum', 'binancecoin', 'matic-network', 'dogecoin', 'cardano', 'polkadot'],
                        vs_currencies='usd')
