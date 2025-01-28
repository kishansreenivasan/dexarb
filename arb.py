import asyncio
import websockets
import json
import aiohttp
import time
from datetime import datetime
from typing import Dict, Set, List, Optional
from decimal import Decimal, ROUND_HALF_UP
import logging
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Exchange(ABC):
    def __init__(self, name: str):
        self.name = name
        self.pairs: Set[str] = set()
        self.prices: Dict[str, Decimal] = {}
        self.ws_endpoint: str = ""
        self.rest_endpoint: str = ""
        
    @abstractmethod
    async def fetch_pairs(self) -> Set[str]:
        pass
        
    @abstractmethod
    async def subscribe_to_trades(self, symbols: Set[str], callback):
        pass
        
    @abstractmethod
    def normalize_pair(self, pair: str) -> str:
        pass

class BinanceUS(Exchange):
    def __init__(self):
        super().__init__("BinanceUS")
        self.ws_endpoint = "wss://stream.binance.us:9443/ws"
        self.rest_endpoint = "https://api.binance.us/api/v3"
        
    async def fetch_pairs(self) -> Set[str]:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.rest_endpoint}/exchangeInfo") as response:
                data = await response.json()
                return {
                    symbol['symbol']
                    for symbol in data.get('symbols', [])
                    if symbol['status'] == 'TRADING'
                }
                
    async def subscribe_to_trades(self, symbols: Set[str], callback):
        streams = [f"{symbol.lower()}@trade" for symbol in symbols]
        stream_path = '/'.join(streams)
        uri = f"{self.ws_endpoint}/{stream_path}"
        
        while True:
            try:
                async with websockets.connect(uri) as ws:
                    logger.info(f"Connected to {self.name} WebSocket")
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        if data.get('e') == 'trade':
                            await callback(self.name, data['s'], Decimal(data['p']), int(data['T']))
            except Exception as e:
                logger.error(f"{self.name} WebSocket error: {e}")
                await asyncio.sleep(5)
                
    def normalize_pair(self, pair: str) -> str:
        return pair.upper()

class Coinbase(Exchange):
    def __init__(self):
        super().__init__("Coinbase")
        self.ws_endpoint = "wss://ws-feed.exchange.coinbase.com"
        self.rest_endpoint = "https://api.exchange.coinbase.com"
        
    async def fetch_pairs(self) -> Set[str]:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.rest_endpoint}/products") as response:
                data = await response.json()
                return {
                    f"{product['base_currency']}{product['quote_currency']}"
                    for product in data
                    if product['status'] == 'online'
                }
                
    async def subscribe_to_trades(self, symbols: Set[str], callback):
        while True:
            try:
                async with websockets.connect(self.ws_endpoint) as ws:
                    logger.info(f"Connected to {self.name} WebSocket")
                    formatted_symbols = [f"{symbol[:-3]}-{symbol[-3:]}" for symbol in symbols]
                    await ws.send(json.dumps({
                        "type": "subscribe",
                        "product_ids": formatted_symbols,
                        "channels": ["matches"]
                    }))
                    
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        if data.get('type') == 'match':
                            symbol = self.normalize_pair(data['product_id'])
                            timestamp = int(datetime.strptime(
                                data['time'], '%Y-%m-%dT%H:%M:%S.%fZ'
                            ).timestamp() * 1000)
                            await callback(self.name, symbol, Decimal(data['price']), timestamp)
            except Exception as e:
                logger.error(f"{self.name} WebSocket error: {e}")
                await asyncio.sleep(5)
                
    def normalize_pair(self, pair: str) -> str:
        return pair.replace('-', '')

class Kraken(Exchange):
    def __init__(self):
        super().__init__("Kraken")
        self.ws_endpoint = "wss://ws.kraken.com"
        self.rest_endpoint = "https://api.kraken.com/0/public"
        
    async def fetch_pairs(self) -> Set[str]:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.rest_endpoint}/AssetPairs") as response:
                data = await response.json()
                return {
                    pair_info['wsname'].replace('/', '')
                    for pair_info in data.get('result', {}).values()
                    if 'wsname' in pair_info
                }
                
    async def subscribe_to_trades(self, symbols: Set[str], callback):
        while True:
            try:
                async with websockets.connect(self.ws_endpoint) as ws:
                    logger.info(f"Connected to {self.name} WebSocket")
                    subscribe_msg = {
                        "event": "subscribe",
                        "pair": list(symbols),
                        "subscription": {"name": "trade"}
                    }
                    await ws.send(json.dumps(subscribe_msg))
                    
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        if isinstance(data, list) and len(data) >= 4:
                            trades = data[1]
                            pair = data[3]
                            for trade in trades:
                                price = Decimal(trade[0])
                                timestamp = int(float(trade[2]) * 1000)
                                await callback(self.name, self.normalize_pair(pair), price, timestamp)
            except Exception as e:
                logger.error(f"{self.name} WebSocket error: {e}")
                await asyncio.sleep(5)
                
    def normalize_pair(self, pair: str) -> str:
        return pair.replace('/', '')

class Gemini(Exchange):
    def __init__(self):
        super().__init__("Gemini")
        self.ws_endpoint = "wss://api.gemini.com/v1/marketdata"
        self.rest_endpoint = "https://api.gemini.com/v1"
        
    async def fetch_pairs(self) -> Set[str]:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.rest_endpoint}/symbols") as response:
                symbols = await response.json()
                return {symbol.upper() for symbol in symbols}
                
    async def subscribe_to_trades(self, symbols: Set[str], callback):
        for symbol in symbols:
            asyncio.create_task(self._subscribe_single_pair(symbol, callback))
            
    async def _subscribe_single_pair(self, symbol: str, callback):
        while True:
            try:
                uri = f"{self.ws_endpoint}/{symbol.lower()}"
                async with websockets.connect(uri) as ws:
                    logger.info(f"Connected to {self.name} WebSocket for {symbol}")
                    while True:
                        msg = await ws.recv()
                        data = json.loads(msg)
                        if data.get('type') == 'trade':
                            events = data.get('events', [])
                            for event in events:
                                if event.get('type') == 'trade':
                                    await callback(
                                        self.name,
                                        symbol,
                                        Decimal(str(event['price'])),
                                        int(event['timestamp'] * 1000)
                                    )
            except Exception as e:
                logger.error(f"{self.name} WebSocket error for {symbol}: {e}")
                await asyncio.sleep(5)
                
    def normalize_pair(self, pair: str) -> str:
        return pair.upper()

class MultiExchangeArbitrage:
    def __init__(self):
        self.exchanges = [
            BinanceUS(),
            Coinbase(),
            Kraken(),
            Gemini()
        ]
        self.price_matrix: Dict[str, Dict[str, Dict]] = {}
        self.min_profit_threshold = Decimal('0.001')  # 0.1%
        self.opportunities_found = 0
        self.last_opportunities = []
        self.max_opportunity_history = 1000
        
    async def initialize(self):
        """Initialize all exchange connections and fetch trading pairs"""
        all_pairs: Dict[str, Set[str]] = {}
        
        # Fetch pairs from all exchanges
        for exchange in self.exchanges:
            try:
                pairs = await exchange.fetch_pairs()
                all_pairs[exchange.name] = pairs
                logger.info(f"Fetched {len(pairs)} pairs from {exchange.name}")
            except Exception as e:
                logger.error(f"Error fetching pairs from {exchange.name}: {e}")
                all_pairs[exchange.name] = set()
                
        # Find common pairs across exchanges
        common_pairs = set.intersection(*all_pairs.values())
        logger.info(f"Found {len(common_pairs)} common pairs across all exchanges")
        
        # Initialize price matrix
        for pair in common_pairs:
            self.price_matrix[pair] = {}
            for exchange in self.exchanges:
                self.price_matrix[pair][exchange.name] = {
                    'price': None,
                    'timestamp': None
                }
                
        return common_pairs

    async def handle_price_update(self, exchange: str, symbol: str, price: Decimal, timestamp: int):
        """Process price updates and check for arbitrage opportunities"""
        if symbol not in self.price_matrix:
            return
            
        self.price_matrix[symbol][exchange] = {
            'price': price,
            'timestamp': timestamp
        }
        
        await self.check_arbitrage_opportunities(symbol)
        await self.check_triangular_arbitrage(symbol)

    async def check_arbitrage_opportunities(self, symbol: str):
        """Check for direct arbitrage opportunities between exchanges"""
        prices = self.price_matrix[symbol]
        valid_prices = {
            ex: data['price']
            for ex, data in prices.items()
            if data['price'] is not None
        }
        
        if len(valid_prices) < 2:
            return
            
        min_price = min(valid_prices.items(), key=lambda x: x[1])
        max_price = max(valid_prices.items(), key=lambda x: x[1])
        
        profit_pct = ((max_price[1] - min_price[1]) / min_price[1]) * Decimal('100')
        
        if profit_pct >= self.min_profit_threshold:
            opportunity = {
                'type': 'direct',
                'symbol': symbol,
                'buy_exchange': min_price[0],
                'sell_exchange': max_price[0],
                'buy_price': float(min_price[1]),
                'sell_price': float(max_price[1]),
                'profit_pct': float(profit_pct),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            }
            await self.log_opportunity(opportunity)

    async def check_triangular_arbitrage(self, symbol: str):
        """Check for triangular arbitrage opportunities"""
        # Example: BTC/USD -> ETH/BTC -> ETH/USD
        quote_currency = symbol[-3:]
        base_currency = symbol[:-3]
        
        for intermediate_symbol in self.price_matrix:
            if intermediate_symbol.endswith(base_currency):
                intermediate_base = intermediate_symbol[:-3]
                reverse_symbol = f"{intermediate_base}{quote_currency}"
                
                if reverse_symbol in self.price_matrix:
                    for exchange in self.exchanges:
                        await self.calculate_triangular_opportunity(
                            exchange.name,
                            symbol,
                            intermediate_symbol,
                            reverse_symbol
                        )

    async def calculate_triangular_opportunity(
        self,
        exchange: str,
        symbol1: str,
        symbol2: str,
        symbol3: str
    ):
        """Calculate potential profit from triangular arbitrage"""
        prices = self.price_matrix
        
        if not all(
            prices.get(s, {}).get(exchange, {}).get('price')
            for s in [symbol1, symbol2, symbol3]
        ):
            return
            
        rate1 = prices[symbol1][exchange]['price']
        rate2 = prices[symbol2][exchange]['price']
        rate3 = prices[symbol3][exchange]['price']
        
        # Calculate theoretical profit
        result = (Decimal('1') / rate1) * (Decimal('1') / rate2) * rate3
        profit_pct = (result - Decimal('1')) * Decimal('100')
        
        if profit_pct >= self.min_profit_threshold:
            opportunity = {
                'type': 'triangular',
                'exchange': exchange,
                'path': [symbol1, symbol2, symbol3],
                'rates': [float(rate1), float(rate2), float(rate3)],
                'profit_pct': float(profit_pct),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            }
            await self.log_opportunity(opportunity)

    async def log_opportunity(self, opportunity: dict):
        """Log and track arbitrage opportunities"""
        self.opportunities_found += 1
        self.last_opportunities.append(opportunity)
        
        if len(self.last_opportunities) > self.max_opportunity_history:
            self.last_opportunities.pop(0)
            
        if opportunity['type'] == 'direct':
            logger.info(f"\nDirect Arbitrage #{self.opportunities_found}")
            logger.info(f"Symbol: {opportunity['symbol']}")
            logger.info(f"Buy at {opportunity['buy_exchange']}: ${opportunity['buy_price']:.8f}")
            logger.info(f"Sell at {opportunity['sell_exchange']}: ${opportunity['sell_price']:.8f}")
            logger.info(f"Potential Profit: {opportunity['profit_pct']:.4f}%")
            
        logger.info("-" * 60)

    async def print_statistics(self):
        """Print periodic statistics about arbitrage opportunities"""
        while True:
            await asyncio.sleep(300)  # Print stats every 5 minutes
            if self.opportunities_found > 0:
                logger.info("\n=== Arbitrage Statistics ===")
                logger.info(f"Total Opportunities Found: {self.opportunities_found}")
                
                if self.last_opportunities:
                    recent_ops = self.last_opportunities[-100:]  # Last 100 opportunities
                    
                    # Separate direct and triangular opportunities
                    direct_ops = [op for op in recent_ops if op['type'] == 'direct']
                    tri_ops = [op for op in recent_ops if op['type'] == 'triangular']
                    
                    if direct_ops:
                        avg_direct_profit = sum(op['profit_pct'] for op in direct_ops) / len(direct_ops)
                        max_direct_profit = max(op['profit_pct'] for op in direct_ops)
                        logger.info(f"\nDirect Arbitrage Stats:")
                        logger.info(f"Average Profit: {avg_direct_profit:.4f}%")
                        logger.info(f"Max Profit: {max_direct_profit:.4f}%")
                    
                    if tri_ops:
                        avg_tri_profit = sum(op['profit_pct'] for op in tri_ops) / len(tri_ops)
                        max_tri_profit = max(op['profit_pct'] for op in tri_ops)
                        logger.info(f"\nTriangular Arbitrage Stats:")
                        logger.info(f"Average Profit: {avg_tri_profit:.4f}%")
                        logger.info(f"Max Profit: {max_tri_profit:.4f}%")
                
                logger.info("=" * 25)

    async def start_exchange_connections(self, common_pairs: Set[str]):
        """Start WebSocket connections for all exchanges"""
        connection_tasks = []
        
        for exchange in self.exchanges:
            connection_tasks.append(
                exchange.subscribe_to_trades(
                    common_pairs,
                    self.handle_price_update
                )
            )
        
        # Add statistics printing task
        connection_tasks.append(self.print_statistics())
        
        # Run all connections concurrently
        await asyncio.gather(*connection_tasks)

    async def run(self):
        """Main execution function"""
        try:
            logger.info("Initializing Multi-Exchange Arbitrage Scanner...")
            common_pairs = await self.initialize()
            
            if not common_pairs:
                logger.error("No common pairs found across exchanges. Exiting...")
                return
                
            logger.info(f"Monitoring {len(common_pairs)} pairs across {len(self.exchanges)} exchanges")
            logger.info(f"Minimum profit threshold: {float(self.min_profit_threshold)}%")
            logger.info("Starting exchange connections...")
            
            # Start monitoring
            await self.start_exchange_connections(common_pairs)
            
        except Exception as e:
            logger.error(f"Error in main execution: {e}")
            raise

def main():
    """Entry point for the arbitrage scanner"""
    try:
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Create and run the arbitrage scanner
        scanner = MultiExchangeArbitrage()
        asyncio.run(scanner.run())
    
    except KeyboardInterrupt:
        logger.info("\nShutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()