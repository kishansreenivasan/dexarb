// pages/api/executeTrade.js
export default function executeTradeHandler(req, res) {
  const { pair } = req.body;
  res.status(200).json({ success: true, profit: 100 });
}
