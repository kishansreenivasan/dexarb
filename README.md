Project Overview -
Create an site that displays arb for any token and executes it.

We monitor the Binance prices and uniswap pools for any possible price discrepancy.

once there is an arbitrage opportunity we use AAVE loans to borrow the currency we need to swap and do the inverse on binance(where we have margin)

We then close the trade by transfering the tokens we bought/sold from/to Binance.

Frontend-
[Use Next.js to create](https://nextjs.org/)

Backend-
Use binance websocket API to pull data from binance.

Use Uniswap subgraph API (JavaScript- Kishan can do this)

If arbitrages exist on this level: meaning large orders(which move the price) aren't arbitraged away inside the block they are placed at (meaning somebody is scanning the mempool(where orders waiting to be executed are displayed)), then onyl these 2 API-s are enough to do the arbitrage

If we want to get more arbitrage opportunities then we can scan the mempool(using the python or rust web3 library) to look at pending transactions and place our orders in the same block.

Open question: in what language do we do the arbitrage calculations(whether to buy, and how much and what should be the gas fee, etc)
and how do we pass the data into it(this is not trivial as making a json file and saving it and then opening it is pretty time consuming, which is a huge consideration) -

Answer: Use Python for calculations and use Redis to pass data in



