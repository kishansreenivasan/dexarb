// components/TokenList.js
import React, { useEffect, useState } from 'react';
import axios from 'axios';

const TokenList = () => {
  const [tokens, setTokens] = useState([]);

  useEffect(() => {
    // Replace with your Uniswap API or other token fetch logic
    const fetchTokens = async () => {
      try {
        const response = await axios.get('/api/tokens');  // Example endpoint
        setTokens(response.data);
      } catch (error) {
        console.error("Error fetching tokens", error);
      }
    };

    fetchTokens();
  }, []);

  return (
    <div>
      <h2 className="text-2xl font-semibold mb-4">Token List</h2>
      <ul className="list-disc pl-6">
        {tokens.map((token, index) => (
          <li key={index} className="text-gray-400">{token.name}</li>
        ))}
      </ul>
    </div>
  );
};

export default TokenList;
