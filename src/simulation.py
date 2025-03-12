from src.uniswap_v3_pool import UniswapV3Pool
from src.token import Token
import math

def run_basic_simulation():
    """Run a basic simulation with a Uniswap V3 pool"""
    
    # Create tokens
    token0 = Token("Ether", "ETH", 18)
    token1 = Token("USD Coin", "USDC", 6)
    
    # Create pool with 0.3% fee
    fee = 0.003
    tick_spacing = 60  # 0.3% fee tier has 60 tick spacing
    
    # Initial price of 1 ETH = 3000 USDC
    initial_price = 3000
    initial_sqrt_price_x96 = int(math.sqrt(initial_price) * 2**96)
    
    pool = UniswapV3Pool(token0, token1, fee, tick_spacing, initial_sqrt_price_x96)
    
    print(f"Created pool {token0} / {token1} with initial price of {initial_price} {token1} per {token0}")
    
    # Add liquidity in different price ranges
    # Wide range position - 2000 to 4000 USDC
    lower_tick_wide = math.floor(math.log(math.sqrt(2000) / math.sqrt(1.0001), math.sqrt(1.0001)))
    upper_tick_wide = math.floor(math.log(math.sqrt(4000) / math.sqrt(1.0001), math.sqrt(1.0001)))
    
    # Medium range position - 2500 to 3500 USDC
    lower_tick_medium = math.floor(math.log(math.sqrt(2500) / math.sqrt(1.0001), math.sqrt(1.0001)))
    upper_tick_medium = math.floor(math.log(math.sqrt(3500) / math.sqrt(1.0001), math.sqrt(1.0001)))
    
    # Narrow range position - 2900 to 3100 USDC
    lower_tick_narrow = math.floor(math.log(math.sqrt(2900) / math.sqrt(1.0001), math.sqrt(1.0001)))
    upper_tick_narrow = math.floor(math.log(math.sqrt(3100) / math.sqrt(1.0001), math.sqrt(1.0001)))
    
    # Add liquidity (use more realistic values)
    liquidity_wide = 1000 * 10**9      # 1000 units of liquidity in the wide range
    liquidity_medium = 5000 * 10**9    # 5000 units of liquidity in the medium range
    liquidity_narrow = 10000 * 10**9   # 10000 units of liquidity in the narrow range
    
    pool.add_position("LP1", lower_tick_wide, upper_tick_wide, liquidity_wide)
    pool.add_position("LP2", lower_tick_medium, upper_tick_medium, liquidity_medium)
    pool.add_position("LP3", lower_tick_narrow, upper_tick_narrow, liquidity_narrow)
    
    print(f"Added liquidity positions:")
    print(f"  LP1: Range ${2000}-${4000}, Liquidity: {liquidity_wide / 10**9:.0f} units")
    print(f"  LP2: Range ${2500}-${3500}, Liquidity: {liquidity_medium / 10**9:.0f} units")
    print(f"  LP3: Range ${2900}-${3100}, Liquidity: {liquidity_narrow / 10**9:.0f} units")
    print(f"Current pool liquidity: {pool.liquidity / 10**9:.0f} units")
    print(f"Current price: ${initial_price}")
    
    # Execute a series of swaps
    print("\nExecuting swaps:")
    
    # Swap 1: Small swap selling ETH for USDC (should decrease ETH price)
    sell_amount = 10 * 10**18  # 10 ETH
    amount0, amount1 = pool.swap(True, sell_amount)
    current_price = (pool.sqrt_price_x96 / 2**96) ** 2
    
    print(f"Swap 1: Sold {amount0 / 10**18:.2f} ETH for {-amount1 / 10**6:.2f} USDC")
    print(f"New price: ${current_price:.2f}")
    print(f"Current liquidity: {pool.liquidity / 10**9:.0f} units")
    
    # Swap 2: Medium swap buying ETH with USDC (should increase ETH price)
    buy_amount = 50000 * 10**6  # 50,000 USDC
    amount0, amount1 = pool.swap(False, buy_amount)
    current_price = (pool.sqrt_price_x96 / 2**96) ** 2
    
    print(f"Swap 2: Sold {amount1 / 10**6:.2f} USDC for {-amount0 / 10**18:.4f} ETH")
    print(f"New price: ${current_price:.2f}")
    print(f"Current liquidity: {pool.liquidity / 10**9:.0f} units")
    
    # Swap 3: Large swap selling ETH for USDC (should significantly decrease ETH price)
    sell_amount = 100 * 10**18  # 100 ETH
    amount0, amount1 = pool.swap(True, sell_amount)
    current_price = (pool.sqrt_price_x96 / 2**96) ** 2
    
    print(f"Swap 3: Sold {amount0 / 10**18:.2f} ETH for {-amount1 / 10**6:.2f} USDC")
    print(f"New price: ${current_price:.2f}")
    print(f"Current liquidity: {pool.liquidity / 10**9:.0f} units")

if __name__ == "__main__":
    run_basic_simulation()