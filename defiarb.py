import asyncio
import aiohttp
import time
import logging
from decimal import Decimal
from datetime import datetime
from typing import Dict, Set, List
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

###############################################################################
# Base Exchange Class
###############################################################################

class Exchange(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def fetch_tokens(self) -> Dict[str, dict]:
        """
        Fetch token data from the exchange.
        Returns a dict mapping token id (lowercase) to a token dict.
        Each token dict should at least contain a symbol and a derivedETH price.
        """
        pass

###############################################################################
# Uniswap DEX (via The Graph)
###############################################################################

class UniswapDEX(Exchange):
    def __init__(self):
        super().__init__("Uniswap")
        self.endpoint = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2"
    
    async def fetch_tokens(self) -> Dict[str, dict]:
        query = """
        {
          tokens(first: 1000) {
            id
            symbol
            derivedETH
          }
        }
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(self.endpoint, json={'query': query}) as response:
                data = await response.json()
                tokens = data.get('data', {}).get('tokens', [])
                # Return a dict keyed by token id (lowercase) for consistency
                return {token['id'].lower(): token 
                        for token in tokens if token.get('derivedETH')}
                        
###############################################################################
# SushiSwap DEX (via The Graph)
###############################################################################

class SushiSwapDEX(Exchange):
    def __init__(self):
        super().__init__("SushiSwap")
        self.endpoint = "https://api.thegraph.com/subgraphs/name/sushiswap/exchange"
    
    async def fetch_tokens(self) -> Dict[str, dict]:
        query = """
        {
          tokens(first: 1000) {
            id
            symbol
            derivedETH
          }
        }
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(self.endpoint, json={'query': query}) as response:
                data = await response.json()
                tokens = data.get('data', {}).get('tokens', [])
                return {token['id'].lower(): token 
                        for token in tokens if token.get('derivedETH')}

###############################################################################
# Multi-Exchange Arbitrage Scanner for DEXes
###############################################################################

class MultiExchangeArbitrage:
    def __init__(self):
        # Use our two DEXes
        self.exchanges = [
            UniswapDEX(),
            SushiSwapDEX()
        ]
        # Price matrix: {token_id: {exchange_name: {'price': Decimal, 'timestamp': int}}}
        self.price_matrix: Dict[str, Dict[str, Dict]] = {}
        # For display, map a token id to its symbol (using the first exchange’s data)
        self.token_symbols: Dict[str, str] = {}
        # Set the minimum arbitrage threshold (in percent)
        self.min_profit_threshold = Decimal('1')  # 1% threshold
        self.opportunities_found = 0
        self.last_opportunities: List[dict] = []
        self.max_opportunity_history = 1000

    async def initialize(self) -> Set[str]:
        """
        Fetch tokens from each DEX and determine the set of tokens common
        to all exchanges.
        """
        all_tokens: Dict[str, Set[str]] = {}
        
        for exchange in self.exchanges:
            try:
                tokens = await exchange.fetch_tokens()
                token_ids = set(tokens.keys())
                all_tokens[exchange.name] = token_ids
                logger.info(f"Fetched {len(token_ids)} tokens from {exchange.name}")
                
                # Save the token symbols from the first exchange we can fetch from.
                if not self.token_symbols and tokens:
                    for tid, token in tokens.items():
                        self.token_symbols[tid] = token.get('symbol', tid)
            except Exception as e:
                logger.error(f"Error fetching tokens from {exchange.name}: {e}")
                all_tokens[exchange.name] = set()
                
        if not all_tokens:
            logger.error("No tokens fetched from any exchange.")
            return set()
            
        # Compute the intersection of token IDs across all exchanges.
        common_tokens = set.intersection(*all_tokens.values())
        logger.info(f"Found {len(common_tokens)} common tokens across exchanges")
        
        # Initialize the price matrix for each common token.
        for token_id in common_tokens:
            self.price_matrix[token_id] = {exchange.name: {'price': None, 'timestamp': None}
                                           for exchange in self.exchanges}
            
        return common_tokens
        
    async def poll_exchange(self, exchange: Exchange):
        """
        Periodically poll a DEX for token prices and update the price matrix.
        """
        while True:
            try:
                tokens = await exchange.fetch_tokens()
                for token_id, token in tokens.items():
                    # Only update if this token is common to all exchanges.
                    if token_id in self.price_matrix:
                        try:
                            price = Decimal(token['derivedETH'])
                        except Exception:
                            continue
                        timestamp = int(time.time() * 1000)
                        self.price_matrix[token_id][exchange.name] = {
                            'price': price,
                            'timestamp': timestamp
                        }
                        await self.check_arbitrage_opportunities(token_id)
            except Exception as e:
                logger.error(f"Error polling {exchange.name}: {e}")
            await asyncio.sleep(10)  # Poll every 10 seconds

    async def check_arbitrage_opportunities(self, token_id: str):
        """
        Check for a direct arbitrage opportunity on a token between the two DEXes.
        """
        prices = self.price_matrix.get(token_id, {})
        valid_prices = {
            ex: data['price']
            for ex, data in prices.items()
            if data['price'] is not None
        }
        
        # Need at least two valid prices to compare.
        if len(valid_prices) < 2:
            return
        
        # Identify the exchange with the lowest and highest price.
        min_exchange, min_price = min(valid_prices.items(), key=lambda x: x[1])
        max_exchange, max_price = max(valid_prices.items(), key=lambda x: x[1])
        
        # Calculate the potential profit percentage.
        profit_pct = ((max_price - min_price) / min_price) * Decimal('100')
        
        if profit_pct >= self.min_profit_threshold:
            opportunity = {
                'type': 'direct',
                'token_id': token_id,
                'symbol': self.token_symbols.get(token_id, token_id),
                'buy_exchange': min_exchange,
                'sell_exchange': max_exchange,
                'buy_price': float(min_price),
                'sell_price': float(max_price),
                'profit_pct': float(profit_pct),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            }
            await self.log_opportunity(opportunity)

    async def log_opportunity(self, opportunity: dict):
        """
        Log (and keep a history of) arbitrage opportunities.
        """
        self.opportunities_found += 1
        self.last_opportunities.append(opportunity)
        if len(self.last_opportunities) > self.max_opportunity_history:
            self.last_opportunities.pop(0)
            
        logger.info(f"\nArbitrage Opportunity #{self.opportunities_found}")
        logger.info(f"Token: {opportunity['symbol']} (ID: {opportunity['token_id']})")
        logger.info(f"Buy at {opportunity['buy_exchange']}: {opportunity['buy_price']:.8f} ETH")
        logger.info(f"Sell at {opportunity['sell_exchange']}: {opportunity['sell_price']:.8f} ETH")
        logger.info(f"Potential Profit: {opportunity['profit_pct']:.4f}%")
        logger.info("-" * 60)

    async def print_statistics(self):
        """
        Periodically print statistics about the arbitrage opportunities.
        """
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            if self.opportunities_found > 0:
                logger.info("\n=== Arbitrage Statistics ===")
                logger.info(f"Total Opportunities Found: {self.opportunities_found}")
                if self.last_opportunities:
                    recent_ops = self.last_opportunities[-100:]
                    avg_profit = sum(op['profit_pct'] for op in recent_ops) / len(recent_ops)
                    max_profit = max(op['profit_pct'] for op in recent_ops)
                    logger.info(f"Average Profit: {avg_profit:.4f}%")
                    logger.info(f"Max Profit: {max_profit:.4f}%")
                logger.info("=" * 25)

    async def start_polling(self, common_tokens: Set[str]):
        """
        Start the polling tasks for all exchanges.
        """
        tasks = []
        for exchange in self.exchanges:
            tasks.append(asyncio.create_task(self.poll_exchange(exchange)))
        tasks.append(asyncio.create_task(self.print_statistics()))
        await asyncio.gather(*tasks)

    async def run(self):
        """
        Main execution function.
        """
        try:
            logger.info("Initializing Decentralized Exchange Arbitrage Scanner...")
            common_tokens = await self.initialize()
            if not common_tokens:
                logger.error("No common tokens found across exchanges. Exiting...")
                return
            logger.info(f"Monitoring {len(common_tokens)} tokens across {len(self.exchanges)} exchanges")
            logger.info(f"Minimum profit threshold: {self.min_profit_threshold}%")
            await self.start_polling(common_tokens)
        except Exception as e:
            logger.error(f"Error in main execution: {e}")
            raise

###############################################################################
# Entry Point
###############################################################################

def main():
    try:
        scanner = MultiExchangeArbitrage()
        asyncio.run(scanner.run())
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == "__main__":
    main()
