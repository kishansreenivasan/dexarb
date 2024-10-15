// components/Footer.js
const Footer = () => {
    return (
      <footer className="bg-pine text-white py-4">
        <div className="container mx-auto text-center">
          <p>&copy; {new Date().getFullYear()} Arbitrage Dashboard. All rights reserved.</p>
        </div>
      </footer>
    );
  };
  
  export default Footer;
  