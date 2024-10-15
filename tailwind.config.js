/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx}', 
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        pine: '#005B5E', // Customize this color code to match Dartmouth's pine green
        white: '#FFFFFF',
      },
    },
  },
  plugins: [],
};
