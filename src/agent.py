import random
import math
import polars as pl
import numpy as np

class Agent:
    """Base class for all trading agents"""
    def __init__(self, name, initial_token0, initial_token1):
        self.name = name
        self.token0_balance = initial_token0
        self.token1_balance = initial_token1
        self.positions = []  # Positions managed by the agent
        self.trade_history = []  # History of trades executed by the agent
        
    def add_position(self, lower_tick, upper_tick, liquidity, pool):
        """Add a new liquidity position"""
        position = {
            'lower_tick': lower_tick,
            'upper_tick': upper_tick,
            'liquidity': liquidity,
            'pool': pool
        }
        self.positions.append(position)
        pool.add_position(self.name, lower_tick, upper_tick, liquidity)
        
    def remove_position(self, position_index, pool):
        """Remove a liquidity position"""
        if position_index < 0 or position_index >= len(self.positions):
            return False
        
        position = self.positions[position_index]
        pool.remove_position(self.name, position['lower_tick'], position['upper_tick'], position['liquidity'])
        self.positions.pop(position_index)
        return True
    
    def execute_swap(self, pool, zero_for_one, amount):
        """Execute a swap on the pool"""
        if zero_for_one and self.token0_balance < amount:
            return False  # Not enough token0 balance
        
        if not zero_for_one and self.token1_balance < amount:
            return False  # Not enough token1 balance
        
        # Execute the swap
        amount0, amount1 = pool.swap(zero_for_one, amount)
        
        # Update agent balances
        self.token0_balance -= amount0
        self.token1_balance -= amount1
        
        # Record the trade
        self.trade_history.append({
            'timestamp': len(self.trade_history),
            'zero_for_one': zero_for_one,
            'amount_in': amount0 if zero_for_one else amount1,
            'amount_out': -amount1 if zero_for_one else -amount0,
            'price': (pool.sqrt_price_x96 / 2**96) ** 2
        })
        
        return True
    
    def act(self, pool, step):
        """
        Agent decides what to do (trade, add/remove liquidity)
        To be implemented by subclasses
        """
        pass
    
    def get_trade_history_df(self):
        """Get trade history as a Polars DataFrame"""
        if not self.trade_history:
            return pl.DataFrame()
        
        return pl.DataFrame(self.trade_history)


class RandomTrader(Agent):
    """Agent that makes random trades"""
    def __init__(self, name, initial_token0, initial_token1, trade_frequency=0.3, max_trade_pct=0.1):
        super().__init__(name, initial_token0, initial_token1)
        self.trade_frequency = trade_frequency  # Probability of trading each step
        self.max_trade_pct = max_trade_pct  # Maximum % of balance to trade
    
    def act(self, pool, step):
        """Randomly decide to trade or not"""
        # Decide whether to trade this step
        if random.random() > self.trade_frequency:
            return  # Don't trade this step
        
        # Decide direction (buy or sell token0)
        zero_for_one = random.choice([True, False])
        
        # Decide amount
        if zero_for_one:
            max_amount = self.token0_balance * self.max_trade_pct
            amount = random.uniform(0, max_amount)
        else:
            max_amount = self.token1_balance * self.max_trade_pct
            amount = random.uniform(0, max_amount)
        
        # Execute trade
        if amount > 0:
            self.execute_swap(pool, zero_for_one, amount)


class TrendFollower(Agent):
    """Agent that follows price trends"""
    def __init__(self, name, initial_token0, initial_token1, window_size=5, threshold=0.02, trade_size_pct=0.2):
        super().__init__(name, initial_token0, initial_token1)
        self.window_size = window_size  # Number of steps to check for trend
        self.threshold = threshold  # Price change threshold to trigger a trade
        self.trade_size_pct = trade_size_pct  # % of balance to trade
        self.price_history = []  # Track price history
    
    def act(self, pool, step):
        """Follow price trends"""
        # Store current price
        current_price = (pool.sqrt_price_x96 / 2**96) ** 2
        self.price_history.append(current_price)
        
        # Need enough price history to detect trend
        if len(self.price_history) < self.window_size:
            return
        
        # Calculate price change over window
        start_price = self.price_history[-self.window_size]
        price_change_pct = (current_price - start_price) / start_price
        
        # If price is trending up, buy token0 (sell token1)
        if price_change_pct > self.threshold:
            amount = self.token1_balance * self.trade_size_pct
            if amount > 0:
                self.execute_swap(pool, False, amount)
        
        # If price is trending down, sell token0 (buy token1)
        elif price_change_pct < -self.threshold:
            amount = self.token0_balance * self.trade_size_pct
            if amount > 0:
                self.execute_swap(pool, True, amount)


class LiquidityProvider(Agent):
    """Agent that provides liquidity around current price"""
    def __init__(self, name, initial_token0, initial_token1, 
                rebalance_frequency=10, position_width=0.1, num_positions=3):
        super().__init__(name, initial_token0, initial_token1)
        self.rebalance_frequency = rebalance_frequency  # Steps between rebalance
        self.position_width = position_width  # Width of each position as % of price
        self.num_positions = num_positions  # Number of positions to maintain
        self.last_rebalance = -rebalance_frequency  # Force initial rebalance
    
    def act(self, pool, step):
        """Manage liquidity positions"""
        # Only rebalance at specified frequency
        if step - self.last_rebalance < self.rebalance_frequency:
            return
        
        try:
            # Remove all existing positions
            for i in range(len(self.positions)-1, -1, -1):
                self.remove_position(i, pool)
            
            # Current price
            current_price = (pool.sqrt_price_x96 / 2**96) ** 2
            
            # Use a minimum price to prevent errors
            current_price = max(0.1, current_price)
            
            # Create positions around current price
            half_width = self.position_width / 2
            
            # Calculate reasonable liquidity amounts based on balances
            # Use a conservative approach to avoid over-committing
            value_in_token0 = min(self.token0_balance, self.token1_balance / current_price)
            liquidity_per_position = value_in_token0 / (self.num_positions * 2)
            liquidity_amount = max(1, int(liquidity_per_position * 10**6))  # Convert to reasonable units
            
            # Calculate ticks for positions distributed around current price
            for i in range(self.num_positions):
                # Calculate a price range relative to current price
                # For simplicity, positions are staggered around current price
                offset = (i - self.num_positions // 2) * self.position_width
                lower_price = current_price * (1 + offset - half_width)
                upper_price = current_price * (1 + offset + half_width)
                
                # Ensure prices are positive
                lower_price = max(0.01, lower_price)
                upper_price = max(lower_price * 1.01, upper_price)
                
                try:
                    # Convert price to ticks
                    lower_tick = math.floor(math.log(math.sqrt(lower_price) / math.sqrt(1.0001), math.sqrt(1.0001)))
                    upper_tick = math.floor(math.log(math.sqrt(upper_price) / math.sqrt(1.0001), math.sqrt(1.0001)))
                    
                    # Ensure the ticks are properly spaced according to pool tick spacing
                    lower_tick = math.floor(lower_tick / pool.tick_spacing) * pool.tick_spacing
                    upper_tick = math.floor(upper_tick / pool.tick_spacing) * pool.tick_spacing
                    
                    # Add position if ticks are valid and provide reasonable range
                    if lower_tick < upper_tick and upper_tick - lower_tick >= pool.tick_spacing:
                        self.add_position(lower_tick, upper_tick, liquidity_amount, pool)
                except (ValueError, ZeroDivisionError):
                    # Skip this position if there's a math error
                    continue
            
            self.last_rebalance = step
        except Exception as e:
            # Log any errors but continue simulation
            print(f"Error in {self.name} agent: {e}")
            pass


class MarketMaker(Agent):
    """
    Advanced market maker with dynamic positioning and risk management
    Uses historical volatility to determine position widths
    """
    def __init__(self, name, initial_token0, initial_token1,
                 rebalance_frequency=20, base_width=0.05,
                 vol_window=50, min_width=0.01, max_width=0.2,
                 inventory_target=0.5, inventory_impact=0.5):
        super().__init__(name, initial_token0, initial_token1)
        self.rebalance_frequency = rebalance_frequency
        self.base_width = base_width
        self.vol_window = vol_window
        self.min_width = min_width
        self.max_width = max_width
        self.inventory_target = inventory_target  # Target % of assets in token0
        self.inventory_impact = inventory_impact  # How much to skew based on inventory
        self.price_history = []
        self.last_rebalance = -rebalance_frequency  # Force initial rebalance
    
    def calculate_volatility(self):
        """Calculate historical volatility"""
        if len(self.price_history) < self.vol_window:
            return self.base_width
        
        try:
            # Calculate log returns
            prices = np.array(self.price_history[-self.vol_window:])
            # Ensure all prices are positive
            prices = np.clip(prices, 0.001, None)
            log_returns = np.diff(np.log(prices))
            
            # Calculate volatility (standard deviation of log returns)
            volatility = np.std(log_returns) * np.sqrt(self.vol_window)
            
            # Scale width based on volatility
            width = self.base_width * (1 + volatility * 10)
            
            return max(self.min_width, min(self.max_width, width))
        except Exception:
            # Fall back to base width if calculation fails
            return self.base_width
    
    def calculate_inventory_ratio(self, current_price):
        """Calculate current inventory ratio"""
        if current_price <= 0:
            return 0.5  # Default to balanced if price is invalid
            
        total_value_in_token0 = self.token0_balance + self.token1_balance / current_price
        if total_value_in_token0 <= 0:
            return 0.5  # Default to balanced if no assets
        
        return self.token0_balance / total_value_in_token0
    
    def act(self, pool, step):
        """Manage market making positions"""
        try:
            # Store current price
            current_price = (pool.sqrt_price_x96 / 2**96) ** 2
            
            # Ensure price is positive
            current_price = max(0.1, current_price)
            self.price_history.append(current_price)
            
            # Only rebalance at specified frequency
            if step - self.last_rebalance < self.rebalance_frequency:
                return
            
            # Remove all existing positions
            for i in range(len(self.positions)-1, -1, -1):
                try:
                    self.remove_position(i, pool)
                except Exception:
                    # Continue even if position removal fails
                    pass
            
            # Calculate position parameters
            width = self.calculate_volatility()
            inv_ratio = self.calculate_inventory_ratio(current_price)
            
            # Skew position based on inventory
            # If we have too much token0, bias towards selling token0
            # If we have too much token1, bias towards selling token1
            skew = (inv_ratio - self.inventory_target) * self.inventory_impact
            
            # Create positions around current price with skew
            lower_price = current_price * (1 - width + skew)
            upper_price = current_price * (1 + width + skew)
            
            # Ensure prices are positive and have a reasonable spread
            lower_price = max(0.01, lower_price)
            upper_price = max(lower_price * 1.01, upper_price)
            
            try:
                # Convert price to ticks
                lower_tick = math.floor(math.log(math.sqrt(lower_price) / math.sqrt(1.0001), math.sqrt(1.0001)))
                upper_tick = math.floor(math.log(math.sqrt(upper_price) / math.sqrt(1.0001), math.sqrt(1.0001)))
                
                # Ensure the ticks are properly spaced according to pool tick spacing
                lower_tick = math.floor(lower_tick / pool.tick_spacing) * pool.tick_spacing
                upper_tick = math.floor(upper_tick / pool.tick_spacing) * pool.tick_spacing
                
                # Calculate a reasonable liquidity amount
                # Use a smaller percentage to avoid over-committing
                value_in_token0 = min(self.token0_balance, self.token1_balance / current_price)
                liquidity_amount = max(1, int(value_in_token0 * 0.5 * 10**6))
                
                # Add position if ticks are valid
                if lower_tick < upper_tick and upper_tick - lower_tick >= pool.tick_spacing:
                    self.add_position(lower_tick, upper_tick, liquidity_amount, pool)
            except (ValueError, ZeroDivisionError):
                # Skip adding position if there's a math error
                pass
            
            self.last_rebalance = step
        except Exception as e:
            # Log any errors but continue simulation
            print(f"Error in MarketMaker agent: {e}")
            pass