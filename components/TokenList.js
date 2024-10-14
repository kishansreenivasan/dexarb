// components/TokenList.js
import React, { useEffect, useState } from "react";
import axios from "axios";

const TokenList = () => {
  const [tokens, setTokens] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch arbitrage opportunities
  const fetchTokens = async () => {
    try {
      const response = await axios.get("/api/getArbOpportunities");
      setTokens(response.data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching tokens", error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTokens();
  }, []);

  const executeTrade = async (tokenPair) => {
    try {
      const response = await axios.post("/api/executeTrade", { pair: tokenPair });
      alert(`Trade executed successfully! Profit: ${response.data.profit}`);
    } catch (error) {
      console.error("Error executing trade", error);
      alert("Trade execution failed.");
    }
  };

  if (loading) {
    return <p>Loading...</p>;
  }

  return (
    <div className="container">
      <h2>Arbitrage Opportunities</h2>
      <table className="table">
        <thead>
          <tr>
            <th>Token Pair</th>
            <th>Uniswap Price</th>
            <th>Binance Price</th>
            <th>Profit %</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {tokens.map((token, index) => (
            <tr key={index}>
              <td>{token.pair}</td>
              <td>{token.uniswapPrice}</td>
              <td>{token.binancePrice}</td>
              <td>{token.profitPercentage}%</td>
              <td>
                <button
                  className="btn btn-success"
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
