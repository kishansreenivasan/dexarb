import { useState, useEffect } from 'react';
import axios from 'axios';

export default function Home() {
  const [binancePrice, setBinancePrice] = useState(null);
  const [uniswapPrice, setUniswapPrice] = useState(null);
  const [arbitrageOpportunity, setArbitrageOpportunity] = useState(null);
  const [buyMessage, setBuyMessage] = useState(null);

  useEffect(() => {
    const fetchPrices = async () => {
      try {
        // Fetch Binance price (or CoinGecko as an alternative)
        const binanceResponse = await axios.get('/api/binance-price');
        const binancePrice = binanceResponse.data.price;
        setBinancePrice(binancePrice);

        // Fetch Uniswap price
        const uniswapResponse = await axios.get('/api/uniswap-price');
        const uniswapPrice = uniswapResponse.data.price;
        setUniswapPrice(uniswapPrice);

        // Calculate arbitrage opportunity
        if (binancePrice && uniswapPrice) {
          const difference = ((binancePrice - uniswapPrice) / uniswapPrice) * 100;
          setArbitrageOpportunity(difference.toFixed(2));
        }
      } catch (error) {
        console.error("Error fetching prices:", error);
      }
    };

    // Initial fetch and interval update
    fetchPrices();
    const interval = setInterval(fetchPrices, 5000);

    return () => clearInterval(interval);
  }, []);

  // Function to handle buy button click
  const handleBuy = () => {
    setBuyMessage("Bought");
  };

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', padding: '2rem' }}>
      <h1>ETH Price Arbitrage</h1>
      <div>
        <h2>Binance Price (USD)</h2>
        <p>{binancePrice ? `$${binancePrice.toFixed(2)}` : 'Loading...'}</p>
      </div>
      <div>
        <h2>Uniswap Price (USD)</h2>
        <p>{uniswapPrice ? `$${uniswapPrice.toFixed(2)}` : 'Loading...'}</p>
      </div>
      <div>
        <h2>Arbitrage Opportunity</h2>
        {arbitrageOpportunity !== null ? (
          <p>
            {arbitrageOpportunity > 0
              ? `Buy on Uniswap, sell on Binance. Potential profit: ${arbitrageOpportunity}%`
              : 'No profitable arbitrage opportunity currently.'}
          </p>
        ) : (
          <p>Calculating arbitrage opportunity...</p>
        )}
      </div>
      <button onClick={handleBuy} style={{ marginTop: '20px', padding: '10px 20px', cursor: 'pointer' }}>
        Buy
      </button>
      {buyMessage && <p>{buyMessage}</p>}
    </div>
  );
}
