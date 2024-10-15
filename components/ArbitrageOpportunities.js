// components/ArbitrageOpportunities.js
import React, { useEffect, useState } from 'react';

const ArbitrageOpportunities = ({ onExecuteClick }) => {
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchOpportunities = async () => {
      // Fetch data from APIs and set it
      setOpportunities([{
        token: 'ETH',
        buyOn: 'Uniswap',
        sellOn: 'Binance',
        profit: 100,
        uniswapPrice: 2000,
        binancePrice: 2100
      }]); // Example data
      setLoading(false);
    };

    fetchOpportunities();
  }, []);

  return (
    <div>
      {loading ? (
        <p>Loading...</p>
      ) : (
        <table className="min-w-full bg-gray-800 shadow-lg rounded-lg">
          <thead>
            <tr className="bg-gray-700 text-left text-sm uppercase text-gray-400">
              <th className="px-6 py-4">Token</th>
              <th className="px-6 py-4">Buy On</th>
              <th className="px-6 py-4">Sell On</th>
              <th className="px-6 py-4">Profit (USD)</th>
              <th className="px-6 py-4">Actions</th>
            </tr>
          </thead>
          <tbody>
            {opportunities.map((opp, index) => (
              <tr key={index} className="border-t border-gray-700">
                <td className="px-6 py-4">{opp.token}</td>
                <td className="px-6 py-4">{opp.buyOn}</td>
                <td className="px-6 py-4">{opp.sellOn}</td>
                <td className="px-6 py-4 text-red-500">${opp.profit}</td>
                <td className="px-6 py-4">
                  <button
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                    onClick={() => onExecuteClick(opp.token)}
                  >
                    Execute
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default ArbitrageOpportunities;
