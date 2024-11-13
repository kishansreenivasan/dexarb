// /pages/api/arbitrage.js
import axios from 'axios';

export default async (req, res) => {
    try {
        // Fetch prices from Binance and Uniswap endpoints
        const [binanceRes, uniswapRes] = await Promise.all([
            axios.get(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/binance-price`),
            axios.get(`${process.env.NEXT_PUBLIC_API_URL || ''}/api/uniswap-price`)
        ]);

        const binancePrice = parseFloat(binanceRes.data.price);
        const uniswapPrice = parseFloat(uniswapRes.data.price);

        console.log("Binance Price:", binancePrice);
        console.log("Uniswap Price:", uniswapPrice);

        // Calculate arbitrage opportunity
        const arbOpportunity = ((binancePrice - uniswapPrice) / uniswapPrice) * 100;
        console.log("Arbitrage Opportunity:", arbOpportunity);

        res.status(200).json({
            binancePrice,
            uniswapPrice,
            arbOpportunity: Math.abs(arbOpportunity),
            message: arbOpportunity > 1 ? 'Arbitrage opportunity exists!' : 'No significant arbitrage opportunity'
        });
    } catch (error) {
        console.error("Error calculating arbitrage opportunity:", error);
        res.status(500).json({ error: "Failed to calculate arbitrage opportunity" });
    }
};
