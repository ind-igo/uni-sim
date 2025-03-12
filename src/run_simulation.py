import math
from src.token import Token
from src.uniswap_v3_pool import UniswapV3Pool
from src.agent import RandomTrader, TrendFollower, LiquidityProvider, MarketMaker
from src.simulator import Simulator

def run_comprehensive_simulation(steps=100):
    """
    Run a comprehensive simulation with multiple agent types
    
    Args:
        steps: Number of simulation steps
    """
    # Create tokens
    eth = Token("Ether", "ETH", 18)
    usdc = Token("USD Coin", "USDC", 6)
    
    # Create pool with 0.3% fee
    fee = 0.003
    tick_spacing = 60  # 0.3% fee tier has 60 tick spacing
    
    # Initial price of 1 ETH = 3000 USDC
    initial_price = 3000
    initial_sqrt_price_x96 = int(math.sqrt(initial_price) * 2**96)
    
    # Create pool
    pool = UniswapV3Pool(eth, usdc, fee, tick_spacing, initial_sqrt_price_x96)
    
    # Create simulator
    simulator = Simulator(pool, initial_price)
    
    # Add base liquidity provider with more conservative parameters
    base_lp = LiquidityProvider(
        name="BaseLiquidity",
        initial_token0=100 * 10**18,   # 100 ETH
        initial_token1=300000 * 10**6, # 300K USDC
        rebalance_frequency=20,
        position_width=0.05,           # Smaller position width
        num_positions=3                # Fewer positions
    )
    simulator.add_agent(base_lp)
    
    # Add random traders
    for i in range(5):
        trader = RandomTrader(
            name=f"RandomTrader_{i}",
            initial_token0=50 * 10**18,  # 50 ETH
            initial_token1=150000 * 10**6,  # 150k USDC
            trade_frequency=0.2,
            max_trade_pct=0.1
        )
        simulator.add_agent(trader)
    
    # Add trend followers
    for i in range(3):
        follower = TrendFollower(
            name=f"TrendFollower_{i}",
            initial_token0=100 * 10**18,  # 100 ETH
            initial_token1=300000 * 10**6,  # 300k USDC
            window_size=5,
            threshold=0.01,
            trade_size_pct=0.2
        )
        simulator.add_agent(follower)
    
    # Add market maker
    market_maker = MarketMaker(
        name="MarketMaker",
        initial_token0=500 * 10**18,  # 500 ETH
        initial_token1=1500000 * 10**6,  # 1.5M USDC
        rebalance_frequency=10,
        base_width=0.05,
        vol_window=20
    )
    simulator.add_agent(market_maker)
    
    # Run simulation
    print(f"Starting comprehensive simulation for {steps} steps")
    simulator.run(steps)
    
    # Get results
    results_df = simulator.get_results_df()
    print("\nSimulation completed!")
    print(f"Final price: ${results_df['price'].tail(1)[0]:.2f}")
    print(f"Price range: ${results_df['price'].min():.2f} - ${results_df['price'].max():.2f}")
    print(f"Average liquidity: {results_df['liquidity'].mean():.0f}")
    
    # Plot results
    try:
        print("\nGenerating plots...")
        simulator.plot_results()
        print("Plots saved to simulation_results.png")
    except Exception as e:
        print(f"Error generating plots: {e}")
    
    # Return simulator for further analysis
    return simulator

if __name__ == "__main__":
    run_comprehensive_simulation(steps=100)