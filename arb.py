import asyncio
import websockets
import json
import aiohttp
import time
from datetime import datetime
from typing import Dict, Set

class CryptoArbitrageTracker:
    def __init__(self):
        self.price_data = {}
        self.binance_pairs: Set[str] = set()
        self.coinbase_pairs: Set[str] = set()
        self.min_price_diff = 0.5  # Minimum price difference to report (%)

    async def fetch_trading_pairs(self):
        """Fetch available trading pairs from both exchanges"""
        async with aiohttp.ClientSession() as session:
            # Fetch Binance.US pairs
            try:
                async with session.get('https://api.binance.us/api/v3/exchangeInfo') as response:
                    data = await response.json()
                    # Print first few symbols for debugging
                    print("\nBinance.US Sample Response:")
                    if 'symbols' in data:
                        print(json.dumps(data['symbols'][:1], indent=2))
                        self.binance_pairs = {
                            symbol['symbol'] 
                            for symbol in data['symbols']
                            if symbol['status'] == 'TRADING'  # Only include active pairs
                        }
                    print(f"Fetched {len(self.binance_pairs)} Binance.US pairs")
                    if self.binance_pairs:
                        print("Sample Binance pairs:", list(self.binance_pairs)[:5])
            except Exception as e:
                print(f"Error fetching Binance.US pairs: {e}")
                self.binance_pairs = set()

            # Fetch Coinbase pairs
            try:
                async with session.get('https://api.exchange.coinbase.com/products') as response:
                    data = await response.json()
                    print("\nCoinbase Sample Response:")
                    if data:
                        print(json.dumps(data[:1], indent=2))
                        self.coinbase_pairs = {
                            f"{product['base_currency']}{product['quote_currency']}"
                            for product in data
                            if product['status'] == 'online'  # Only include active pairs
                        }
                    print(f"Fetched {len(self.coinbase_pairs)} Coinbase pairs")
                    if self.coinbase_pairs:
                        print("Sample Coinbase pairs:", list(self.coinbase_pairs)[:5])
            except Exception as e:
                print(f"Error fetching Coinbase pairs: {e}")
                self.coinbase_pairs = set()

        # Find common pairs
        common_pairs = self.binance_pairs.intersection(self.coinbase_pairs)
        print(f"\nFound {len(common_pairs)} common pairs")
        if common_pairs:
            print("Sample common pairs:", list(common_pairs)[:5])
        return common_pairs

    def normalize_pair(self, pair: str, exchange: str) -> str:
        """Normalize trading pair format between exchanges"""
        if exchange == 'binance':
            return pair.upper()
        # For Coinbase, convert from BASE-QUOTE to BASEQUOTE format
        return pair.replace('-', '')

    def calculate_price_difference(self, symbol: str) -> dict:
        """Calculate price difference percentage between exchanges"""
        data = self.price_data.get(symbol, {})
        if 'binance' in data and 'coinbase' in data:
            binance_price = data['binance']['price']
            coinbase_price = data['coinbase']['price']
            if binance_price and coinbase_price:
                diff_pct = ((coinbase_price - binance_price) / binance_price) * 100
                return {
                    'symbol': symbol,
                    'binance_price': binance_price,
                    'coinbase_price': coinbase_price,
                    'difference': diff_pct,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                }
        return None

    def print_opportunity(self, data: dict):
        """Print arbitrage opportunity if difference exceeds threshold"""
        if abs(data['difference']) >= self.min_price_diff:
            print(f"\nArbitrage Opportunity Found! {data['timestamp']}")
            print(f"Symbol: {data['symbol']}")
            print(f"Binance.US: ${data['binance_price']:.4f}")
            print(f"Coinbase:   ${data['coinbase_price']:.4f}")
            print(f"Difference: {data['difference']:.2f}%")
            print("-" * 50)

    async def handle_binance_message(self, message: str):
        """Process Binance.US WebSocket messages"""
        try:
            data = json.loads(message)
            if data.get('e') == 'trade':
                symbol = data['s']
                price = float(data['p'])
                
                if symbol not in self.price_data:
                    self.price_data[symbol] = {}
                
                self.price_data[symbol]['binance'] = {
                    'price': price,
                    'timestamp': data['T']
                }

                diff_data = self.calculate_price_difference(symbol)
                if diff_data:
                    self.print_opportunity(diff_data)
        except Exception as e:
            print(f"Error handling Binance message: {e}")

    async def handle_coinbase_message(self, message: str):
        """Process Coinbase WebSocket messages"""
        try:
            data = json.loads(message)
            if data.get('type') == 'match':
                symbol = self.normalize_pair(data['product_id'], 'coinbase')
                price = float(data['price'])
                
                if symbol not in self.price_data:
                    self.price_data[symbol] = {}
                
                self.price_data[symbol]['coinbase'] = {
                    'price': price,
                    'timestamp': time.time() * 1000
                }

                diff_data = self.calculate_price_difference(symbol)
                if diff_data:
                    self.print_opportunity(diff_data)
        except Exception as e:
            print(f"Error handling Coinbase message: {e}")

    async def binance_websocket(self, symbols: Set[str]):
        """Maintain Binance.US WebSocket connection"""
        # Create separate streams for each symbol
        streams = [f"{symbol.lower()}@trade" for symbol in symbols]
        # Join all streams with forward slash
        stream_path = '/'.join(streams)
        uri = f"wss://stream.binance.us:9443/ws/{stream_path}"
        
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    print(f"\nConnected to Binance.US WebSocket")
                    print(f"Monitoring {len(symbols)} pairs")
                    
                    while True:
                        message = await websocket.recv()
                        await self.handle_binance_message(message)
            except Exception as e:
                print(f"Binance.US WebSocket error: {e}")
                await asyncio.sleep(5)  # Wait before reconnecting

    async def coinbase_websocket(self, symbols: Set[str]):
        """Maintain Coinbase WebSocket connection"""
        uri = "wss://ws-feed.exchange.coinbase.com"
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    print(f"\nConnected to Coinbase WebSocket")
                    # Convert symbols to Coinbase format (e.g., BTCUSD -> BTC-USD)
                    formatted_symbols = [
                        f"{symbol[:-3]}-{symbol[-3:]}" 
                        for symbol in symbols
                    ]
                    subscribe_msg = {
                        "type": "subscribe",
                        "product_ids": formatted_symbols,
                        "channels": ["matches"]
                    }
                    await websocket.send(json.dumps(subscribe_msg))
                    print(f"Monitoring {len(symbols)} pairs")
                    
                    while True:
                        message = await websocket.recv()
                        await self.handle_coinbase_message(message)
            except Exception as e:
                print(f"Coinbase WebSocket error: {e}")
                await asyncio.sleep(5)  # Wait before reconnecting

    async def run(self):
        """Main execution function"""
        try:
            common_pairs = await self.fetch_trading_pairs()
            if not common_pairs:
                print("No common pairs found. Exiting...")
                return
            
            # Start WebSocket connections
            await asyncio.gather(
                self.binance_websocket(common_pairs),
                self.coinbase_websocket(common_pairs)
            )
        except Exception as e:
            print(f"Error in main execution: {e}")

if __name__ == "__main__":
    print("Starting Crypto Arbitrage Tracker...")
    tracker = CryptoArbitrageTracker()
    asyncio.run(tracker.run())