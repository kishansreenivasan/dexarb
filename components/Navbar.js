// components/Navbar.js
import Link from 'next/link';

const Navbar = () => {
  return (
    <nav className="bg-pine p-4 shadow-md">
      <div className="container mx-auto flex justify-between items-center">
        <div className="text-white font-bold text-xl">
          Arbitrage Dashboard
        </div>
        <ul className="flex space-x-4">
          <li>
            <Link href="/" className="text-gray-300 hover:text-white transition duration-200">
              Home
            </Link>
          </li>
          <li>
            <Link href="/dashboard" className="text-gray-300 hover:text-white transition duration-200">
              Dashboard
            </Link>
          </li>
        </ul>
      </div>
    </nav>
  );
};

export default Navbar;
