// pages/dashboard.js
import React, { useState } from 'react';
import Navbar from '../components/Navbar';
import ArbitrageOpportunities from '../components/ArbitrageOpportunities.js';
import ExecuteModel from '../components/Executemodel';

const Dashboard = () => {
  const [isModalOpen, setModalOpen] = useState(false);
  const [selectedToken, setSelectedToken] = useState(null);

  const handleExecuteClick = (token) => {
    setSelectedToken(token);
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
  };

  const executeTrade = (token) => {
    console.log(`Executing trade for ${token}`);
    setModalOpen(false);
    // Logic to trigger trade execution goes here
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <Navbar />
      <main className="container mx-auto px-6 py-8">
        <ArbitrageOpportunities onExecuteClick={handleExecuteClick} />
      </main>

      <ExecuteModel
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        token={selectedToken}
        executeTrade={executeTrade}
      />
    </div>
  );
};

export default Dashboard;
