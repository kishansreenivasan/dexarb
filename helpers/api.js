// utils/api.js
import axios from "axios";

export const getArbOpportunities = async () => {
  try {
    const response = await axios.get("/api/getArbOpportunities");
    return response.data;
  } catch (error) {
    console.error("Error fetching arbitrage opportunities", error);
    return [];
  }
};

export const executeTrade = async (tokenPair) => {
  try {
    const response = await axios.post("/api/executeTrade", { pair: tokenPair });
    return response.data;
  } catch (error) {
    console.error("Error executing trade", error);
    throw error;
  }
};
