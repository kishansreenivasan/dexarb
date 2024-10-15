// pages/api/executeTrade.js
export default function handler(req, res) {
  const { pair } = req.body;

  // Mocked opportunities (should match those in getArbOpportunities)
  const opportunities = [
    { pair: "ETH/USDT", uniswapPrice: 3400, binancePrice: 3450 },
    { pair: "BTC/USDT", uniswapPrice: 55000, binancePrice: 55200 },
  ];

  const opportunity = opportunities.find((opp) => opp.pair === pair);

  if (opportunity) {
    const priceDifference = opportunity.binancePrice - opportunity.uniswapPrice;
    res.status(200).json({
      success: true,
      priceDifference: priceDifference,
      message: `Trade executed successfully! Price difference: $${priceDifference}`,
    });
  } else {
    res.status(400).json({ success: false, message: "Invalid token pair" });
  }
}
