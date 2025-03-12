import polars as pl
from src.uniswap_v3_pool import UniswapV3Pool
from src.token import Token
import math
import matplotlib.pyplot as plt

class Simulator:
    """Simulation environment for Uniswap V3 with multiple agents"""
    
    def __init__(self, pool, initial_price):
        """
        Initialize the simulator
        
        Args:
            pool: UniswapV3Pool instance
            initial_price: Initial price of token0 in terms of token1
        """
        self.pool = pool
        self.initial_price = initial_price
        self.agents = []
        self.price_history = []
        self.liquidity_history = []
        self.volume_history = []
        self.step_count = 0
    
    def add_agent(self, agent):
        """Add an agent to the simulation"""
        self.agents.append(agent)
    
    def run(self, steps):
        """Run the simulation for a given number of steps"""
        for step in range(steps):
            self.step_count += 1
            
            # Record state before actions
            price = (self.pool.sqrt_price_x96 / 2**96) ** 2
            price = max(0.01, price)  # Ensure price is positive
            self.price_history.append(price)
            
            # Ensure liquidity is never negative
            self.pool.liquidity = max(0, self.pool.liquidity)
            self.liquidity_history.append(self.pool.liquidity / 10**9)
            
            # Track volume in this step
            step_volume = 0
            
            # Let each agent act
            for agent in self.agents:
                # Record balance before action
                token0_before = agent.token0_balance
                token1_before = agent.token1_balance
                
                # Agent takes action
                agent.act(self.pool, self.step_count)
                
                # Calculate volume from this agent's actions (approximate in token1 value)
                token0_diff = abs(agent.token0_balance - token0_before)
                token1_diff = abs(agent.token1_balance - token1_before)
                volume = token0_diff * price + token1_diff
                step_volume += volume
            
            self.volume_history.append(step_volume)
            
            # Option to print status
            if (step + 1) % 10 == 0:
                print(f"Step {step+1}/{steps}: Price = ${price:.2f}, Liquidity = {self.pool.liquidity / 10**9:.0f}")
    
    def get_results_df(self):
        """Get simulation results as a Polars DataFrame"""
        data = {
            'step': list(range(self.step_count)),
            'price': self.price_history,
            'liquidity': self.liquidity_history,
            'volume': self.volume_history
        }
        
        return pl.DataFrame(data)
    
    def plot_results(self):
        """Plot simulation results"""
        # Create the figure with 3 subplots
        fig, axs = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
        
        # Plot price
        axs[0].plot(self.price_history)
        axs[0].set_title('Price History')
        axs[0].set_ylabel('Price')
        axs[0].grid(True)
        
        # Plot liquidity
        axs[1].plot(self.liquidity_history)
        axs[1].set_title('Liquidity History')
        axs[1].set_ylabel('Liquidity')
        axs[1].grid(True)
        
        # Plot volume
        axs[2].bar(range(len(self.volume_history)), self.volume_history)
        axs[2].set_title('Trading Volume')
        axs[2].set_xlabel('Step')
        axs[2].set_ylabel('Volume')
        axs[2].grid(True)
        
        plt.tight_layout()
        plt.savefig('simulation_results.png')
        
        return fig, axs