// /pages/api/binance-price.js
import axios from 'axios';

export default async (req, res) => {
  try {
    // Fetch ETH price from CoinGecko as an alternative
    const response = await axios.get(
      'https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd'
    );
    const price = response.data.ethereum.usd;
    res.status(200).json({ price });
  } catch (error) {
    console.error("Error fetching CoinGecko price:", error);
    res.status(500).json({ error: "Failed to fetch price" });
  }
};
