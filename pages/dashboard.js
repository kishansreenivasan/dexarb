// pages/dashboard.js
import React from "react";
import Navbar from "../components/Navbar";
import TokenList from "../components/Tokenlist";

const Dashboard = () => {
  return (
    <div>
      <Navbar />
      <TokenList />
    </div>
  );
};

export default Dashboard;
