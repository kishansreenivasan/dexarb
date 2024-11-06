import os
import time
from binance.client import Client as BinanceClient
from uniswap import Uniswap
from web3 import Web3

# Binance setup
BINANCE_API_KEY = 'your_binance_api_key'
BINANCE_API_SECRET = 'your_binance_api_secret'
binance_client = BinanceClient(BINANCE_API_KEY, BINANCE_API_SECRET)

# Uniswap setup
UNISWAP_ADDRESS = 'your_uniswap_wallet_address'
PRIVATE_KEY = 'your_private_key'
w3 = Web3(Web3.HTTPProvider("https://mainnet.infura.io/v3/your_infura_project_id"))
uniswap_client = Uniswap(address=UNISWAP_ADDRESS, private_key=PRIVATE_KEY, version=2, web3=w3)

# Parameters
TRADING_PAIR = 'ETHUSDT'  # Example trading pair

def get_binance_price():
    """Fetch ETH/USDT price from Binance."""
    ticker = binance_client.get_symbol_ticker(symbol=TRADING_PAIR)
    return float(ticker['price'])

def get_uniswap_price():
    """Fetch ETH/USDT price from Uniswap."""
    eth_address = w3.toChecksumAddress("0x0000000000000000000000000000000000000000")  # ETH address
    usdt_address = w3.toChecksumAddress("0xdAC17F958D2ee523a2206206994597C13D831ec7")  # USDT address
    eth_to_usdt_price = uniswap_client.get_price_input(eth_address, usdt_address, 10**18) / 10**6  # Price in USDT
    return eth_to_usdt_price

def check_arbitrage():
    binance_price = get_binance_price()
    uniswap_price = get_uniswap_price()
    
    print(f"Binance Price: {binance_price} USDT")
    print(f"Uniswap Price: {uniswap_price} USDT")
    
    # Calculate arbitrage opportunity
    if binance_price < uniswap_price:
        profit_percentage = ((uniswap_price - binance_price) / binance_price) * 100
        print(f"Arbitrage Opportunity: Buy on Binance, Sell on Uniswap ({profit_percentage:.2f}% profit)")
    elif uniswap_price < binance_price:
        profit_percentage = ((binance_price - uniswap_price) / uniswap_price) * 100
        print(f"Arbitrage Opportunity: Buy on Uniswap, Sell on Binance ({profit_percentage:.2f}% profit)")
    else:
        print("No arbitrage opportunity found.")

# Continuous Monitoring
while True:
    check_arbitrage()
    time.sleep(10)  # Check every 10 seconds
