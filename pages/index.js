// pages/index.js
import React from "react";
import Navbar from "../components/Navbar";

const Home = () => {
  return (
    <div>
      <Navbar />
      <div className="container text-center" style={{ marginTop: "50px" }}>
        <h1>Welcome to Arb Finder</h1>
        <p>Monitor arbitrage opportunities and execute profitable trades.</p>
        <a href="/dashboard" className="btn btn-primary">
          Go to Dashboard
        </a>
      </div>
    </div>
  );
};

export default Home;
