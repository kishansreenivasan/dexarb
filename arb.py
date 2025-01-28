import asyncio
import websockets
import json
import aiohttp
import time
from datetime import datetime
from typing import Dict, Set
from decimal import Decimal, ROUND_HALF_UP
import decimal

class EnhancedCryptoArbitrageTracker:
    def __init__(self):
        self.price_data = {}
        self.binance_pairs: Set[str] = set()
        self.coinbase_pairs: Set[str] = set()
        self.min_price_diff = 0.001  # Now detecting 0.001% differences
        self.opportunities_found = 0
        self.last_opportunities = []
        self.max_opportunity_history = 1000

    def normalize_pair(self, pair: str, exchange: str) -> str:
        """Normalize trading pair format between exchanges"""
        if exchange == 'binance':
            return pair.upper()
        # For Coinbase, convert from BASE-QUOTE to BASEQUOTE format
        return pair.replace('-', '')

    async def fetch_trading_pairs(self):
        """Fetch available trading pairs from both exchanges with expanded criteria"""
        async with aiohttp.ClientSession() as session:
            # Fetch Binance.US pairs with expanded criteria
            try:
                async with session.get('https://api.binance.us/api/v3/exchangeInfo') as response:
                    data = await response.json()
                    self.binance_pairs = {
                        symbol['symbol'] 
                        for symbol in data.get('symbols', [])
                        if symbol['status'] == 'TRADING'
                        and not symbol.get('permissions', ['NONE'])[0] == 'CONDITIONAL_TRADING'
                    }
                    print(f"Fetched {len(self.binance_pairs)} Binance.US pairs")
            except Exception as e:
                print(f"Error fetching Binance.US pairs: {e}")
                self.binance_pairs = set()

            # Fetch Coinbase pairs with expanded criteria
            try:
                async with session.get('https://api.exchange.coinbase.com/products') as response:
                    data = await response.json()
                    self.coinbase_pairs = {
                        f"{product['base_currency']}{product['quote_currency']}"
                        for product in data
                        if product['status'] == 'online'
                        and product.get('trading_disabled') is False
                        and product.get('cancel_only') is False
                    }
                    print(f"Fetched {len(self.coinbase_pairs)} Coinbase pairs")
            except Exception as e:
                print(f"Error fetching Coinbase pairs: {e}")
                self.coinbase_pairs = set()

        common_pairs = self.binance_pairs.intersection(self.coinbase_pairs)
        print(f"\nFound {len(common_pairs)} common pairs")
        return common_pairs

    def calculate_price_difference(self, symbol: str) -> dict:
        """Calculate precise price difference using Decimal for higher accuracy"""
        data = self.price_data.get(symbol, {})
        if 'binance' in data and 'coinbase' in data:
            try:
                binance_price = Decimal(str(data['binance']['price']))
                coinbase_price = Decimal(str(data['coinbase']['price']))
                
                if binance_price and coinbase_price:
                    diff_pct = ((coinbase_price - binance_price) / binance_price * Decimal('100')).quantize(
                        Decimal('0.00000001'), rounding=ROUND_HALF_UP
                    )
                    
                    timestamp = datetime.fromtimestamp(data['binance']['timestamp'] / 1000)
                    latency = abs(data['binance']['timestamp'] - data['coinbase']['timestamp'])
                    
                    return {
                        'symbol': symbol,
                        'binance_price': float(binance_price),
                        'coinbase_price': float(coinbase_price),
                        'difference': float(diff_pct),
                        'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                        'latency_ms': latency
                    }
            except (ValueError, TypeError, decimal.InvalidOperation) as e:
                print(f"Error calculating price difference for {symbol}: {e}")
        return None

    def print_opportunity(self, data: dict):
        """Print arbitrage opportunity with enhanced information"""
        if abs(data['difference']) >= self.min_price_diff:
            self.opportunities_found += 1
            self.last_opportunities.append(data)
            if len(self.last_opportunities) > self.max_opportunity_history:
                self.last_opportunities.pop(0)
            
            print(f"\nArbitrage Opportunity #{self.opportunities_found} | {data['timestamp']}")
            print(f"Symbol: {data['symbol']}")
            print(f"Binance.US: ${data['binance_price']:.8f}")
            print(f"Coinbase:   ${data['coinbase_price']:.8f}")
            print(f"Difference: {data['difference']:.6f}%")
            print(f"Data Latency: {data['latency_ms']:.2f}ms")
            
            standard_trade = 1000  # $1000 USD
            potential_profit = (standard_trade * abs(data['difference'])) / 100
            print(f"Potential Profit (${standard_trade} trade): ${potential_profit:.4f}")
            print("-" * 60)

    async def handle_binance_message(self, message: str):
        """Process Binance.US WebSocket messages with enhanced error handling"""
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
        except json.JSONDecodeError as e:
            print(f"JSON decode error in Binance message: {e}")
        except Exception as e:
            print(f"Error handling Binance message: {e}")

    async def handle_coinbase_message(self, message: str):
        """Process Coinbase WebSocket messages with enhanced error handling"""
        try:
            data = json.loads(message)
            if data.get('type') == 'match':
                symbol = self.normalize_pair(data['product_id'], 'coinbase')
                price = float(data['price'])
                
                if symbol not in self.price_data:
                    self.price_data[symbol] = {}
                
                # Convert ISO timestamp to milliseconds
                timestamp = datetime.strptime(data['time'], '%Y-%m-%dT%H:%M:%S.%fZ')
                timestamp_ms = int(timestamp.timestamp() * 1000)
                
                self.price_data[symbol]['coinbase'] = {
                    'price': price,
                    'timestamp': timestamp_ms
                }

                diff_data = self.calculate_price_difference(symbol)
                if diff_data:
                    self.print_opportunity(diff_data)
        except json.JSONDecodeError as e:
            print(f"JSON decode error in Coinbase message: {e}")
        except Exception as e:
            print(f"Error handling Coinbase message: {e}")

    async def binance_websocket(self, symbols: Set[str]):
        """Maintain Binance.US WebSocket connection"""
        streams = [f"{symbol.lower()}@trade" for symbol in symbols]
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

    async def print_statistics(self):
        """Periodically print trading statistics"""
        while True:
            await asyncio.sleep(300)  # Print stats every 5 minutes
            if self.opportunities_found > 0:
                print("\n=== Arbitrage Statistics ===")
                print(f"Total Opportunities Found: {self.opportunities_found}")
                if self.last_opportunities:
                    recent_diffs = [abs(opp['difference']) for opp in self.last_opportunities[-100:]]
                    avg_diff = sum(recent_diffs) / len(recent_diffs)
                    max_diff = max(recent_diffs)
                    print(f"Average Recent Difference: {avg_diff:.6f}%")
                    print(f"Maximum Recent Difference: {max_diff:.6f}%")
                print("=" * 25)

    async def run(self):
        """Main execution function with enhanced monitoring"""
        try:
            common_pairs = await self.fetch_trading_pairs()
            if not common_pairs:
                print("No common pairs found. Exiting...")
                return
            
            await asyncio.gather(
                self.binance_websocket(common_pairs),
                self.coinbase_websocket(common_pairs),
                self.print_statistics()
            )
        except Exception as e:
            print(f"Error in main execution: {e}")

if __name__ == "__main__":
    print("Starting Enhanced Crypto Arbitrage Tracker...")
    print("Monitoring for opportunities with 0.001% or greater difference")
    tracker = EnhancedCryptoArbitrageTracker()
    asyncio.run(tracker.run())