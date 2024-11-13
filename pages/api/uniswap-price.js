// /pages/api/uniswap-price.js
import { ethers } from 'ethers';

const INFURA_API_KEY = process.env.NEXT_PUBLIC_INFURA_API_KEY;
const provider = new ethers.JsonRpcProvider(`https://mainnet.infura.io/v3/${INFURA_API_KEY}`);

// Uniswap V3 Pool address for ETH/USDC
const POOL_ADDRESS = '0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8';

const POOL_ABI = [
  "function slot0() external view returns (uint160 sqrtPriceX96, int24 tick, uint16 observationIndex, uint16 observationCardinality, uint16 observationCardinalityNext, uint8 feeProtocol, bool unlocked)"
];

export default async (req, res) => {
  try {
    const poolContract = new ethers.Contract(POOL_ADDRESS, POOL_ABI, provider);
    const slot0 = await poolContract.slot0();
    const sqrtPriceX96 = slot0[0];

    // Convert sqrtPriceX96 to a usable price format
    const price = (Number(sqrtPriceX96) ** 2) / (2 ** 192) / 1e6;

    res.status(200).json({ price });
  } catch (error) {
    console.error('Error fetching Uniswap price:', error);
    res.status(500).json({ error: 'Failed to fetch Uniswap price' });
  }
};
