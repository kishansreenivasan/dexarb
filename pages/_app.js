// pages/_app.js
import 'bootstrap/dist/css/bootstrap.min.css';
import '../helpers/global.css';

function MyApp({ Component, pageProps }) {
  return <Component {...pageProps} />;
}

export default MyApp;
