// pages/index.js
import React from "react";
import Navbar from "../components/Navbar";
import TokenList from "../components/TokenList";

const IndexPage = () => {
  return (
    <div className="min-h-screen bg-gray-100">
      <Navbar />
      <div className="container mx-auto px-4 py-10">
        <h1 className="text-4xl font-bold text-center text-green-800 mb-8">
          Welcome to the Arbitrage Dashboard
        </h1>
        <div className="bg-white shadow-lg rounded-lg p-6">
          <h2 className="text-2xl font-semibold mb-4 text-center">
            Current Arbitrage Opportunities
          </h2>
          <TokenList />
        </div>
      </div>
    </div>
  );
};

export default IndexPage;
