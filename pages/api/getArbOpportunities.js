// pages/api/getArbOpportunities.js
export default function getArbOpportunitiesHandler(req, res) {
  const opportunities = [
    { pair: "ETH/USDT", uniswapPrice: 3400, binancePrice: 3450, profitPercentage: 1.5 },
    { pair: "BTC/USDT", uniswapPrice: 55000, binancePrice: 55200, profitPercentage: 0.4 },
  ];
  res.status(200).json(opportunities);
}
