// components/TokenList.js
import React, { useEffect, useState } from "react";
import axios from "axios";

const TokenList = () => {
  const [tokens, setTokens] = useState([]);

  // Fetch arbitrage opportunities
  const fetchTokens = async () => {
    try {
      const response = await axios.get("/api/getArbOpportunities");  // Backend route for opportunities
      setTokens(response.data);
    } catch (error) {
      console.error("Error fetching tokens", error);
    }
  };

  useEffect(() => {
    fetchTokens();
  }, []);

  // Execute trade and display price difference
  const executeTrade = async (tokenPair) => {
    try {
      const response = await axios.post("/api/executeTrade", { pair: tokenPair });
      if (response.data.success) {
        alert(`Trade executed successfully! Price difference: $${response.data.priceDifference}`);
      } else {
        alert(response.data.message);
      }
    } catch (error) {
      console.error("Error executing trade", error);
      alert("Trade execution failed.");
    }
  };

  return (
    <div className="container">
      <h2 className="text-2xl font-semibold mb-4">Arbitrage Opportunities</h2>
      <table className="table-auto w-full">
        <thead>
          <tr>
            <th className="px-4 py-2">Token Pair</th>
            <th className="px-4 py-2">Uniswap Price</th>
            <th className="px-4 py-2">Binance Price</th>
            <th className="px-4 py-2">Profit %</th>
            <th className="px-4 py-2">Action</th>
          </tr>
        </thead>
        <tbody>
          {tokens.map((token, index) => (
            <tr key={index}>
              <td className="border px-4 py-2">{token.pair}</td>
              <td className="border px-4 py-2">${token.uniswapPrice}</td>
              <td className="border px-4 py-2">${token.binancePrice}</td>
              <td className="border px-4 py-2">{token.profitPercentage}%</td>
              <td className="border px-4 py-2">
                <button
                  className="btn btn-success bg-green-500 text-white px-4 py-2 rounded"
                  onClick={() => executeTrade(token.pair)}
                >
                  Execute Trade
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TokenList;
