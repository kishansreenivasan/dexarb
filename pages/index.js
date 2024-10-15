// pages/index.js
import Link from 'next/link';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer'; // Import the Footer component

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 flex flex-col">
      <Navbar />
      <main className="container mx-auto flex-grow px-6 py-16 text-center">
        <h1 className="text-6xl font-bold mb-6">Welcome to the Arbitrage Dashboard</h1>
        <p className="text-lg mb-8">
          Track and execute arbitrage opportunities for tokens across Uniswap and Binance.
        </p>
        <Link href="/dashboard" className="inline-block px-8 py-4 bg-pine text-white rounded hover:bg-opacity-80 transition duration-200">
          Go to Dashboard
        </Link>
      </main>
      <Footer />
    </div>
  );
}
