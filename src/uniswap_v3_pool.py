import math

class UniswapV3Pool:
    def __init__(self, token0, token1, fee, tick_spacing, initial_sqrt_price):
        """
        Initialize a Uniswap V3 pool
        
        Args:
            token0: First token in the pair
            token1: Second token in the pair
            fee: Fee tier (e.g., 0.003 for 0.3%)
            tick_spacing: Tick spacing for this fee tier
            initial_sqrt_price: Initial sqrt price as Q64.96
        """
        self.token0 = token0
        self.token1 = token1
        self.fee = fee
        self.tick_spacing = tick_spacing
        self.sqrt_price_x96 = initial_sqrt_price
        self.liquidity = 0
        self.tick = self.get_tick_at_sqrt_price(initial_sqrt_price)
        self.positions = {}
        self.ticks = {}
    
    def get_tick_at_sqrt_price(self, sqrt_price_x96):
        """Convert sqrt price to tick index"""
        try:
            price_value = sqrt_price_x96 / (2**96)
            if price_value <= 0:
                return -887272  # Min tick
            return math.floor(math.log(price_value, math.sqrt(1.0001)))
        except (ValueError, ZeroDivisionError):
            if sqrt_price_x96 <= 0:
                return -887272  # Min tick
            return 887272  # Max tick
    
    def get_sqrt_price_at_tick(self, tick):
        """Convert tick index to sqrt price"""
        tick = max(-887272, min(tick, 887272))  # Clamp to valid range
        return int(1.0001 ** (tick / 2) * (2**96))
    
    def add_position(self, owner, lower_tick, upper_tick, amount):
        """
        Add liquidity position
        
        Args:
            owner: Position owner
            lower_tick: Lower tick boundary
            upper_tick: Upper tick boundary
            amount: Liquidity amount
        """
        # Ensure ticks are properly spaced
        lower_tick = math.floor(lower_tick / self.tick_spacing) * self.tick_spacing
        upper_tick = math.floor(upper_tick / self.tick_spacing) * self.tick_spacing
        
        # Create position key
        position_key = (owner, lower_tick, upper_tick)
        
        # Update position
        if position_key in self.positions:
            self.positions[position_key] += amount
        else:
            self.positions[position_key] = amount
        
        # Update tick data
        if lower_tick not in self.ticks:
            self.ticks[lower_tick] = 0
        if upper_tick not in self.ticks:
            self.ticks[upper_tick] = 0
        
        self.ticks[lower_tick] += amount
        self.ticks[upper_tick] -= amount
        
        # Update pool liquidity if position is in range
        if lower_tick <= self.tick < upper_tick:
            self.liquidity += amount
    
    def remove_position(self, owner, lower_tick, upper_tick, amount):
        """Remove liquidity position"""
        position_key = (owner, lower_tick, upper_tick)
        
        if position_key not in self.positions or self.positions[position_key] < amount:
            raise ValueError("Position does not exist or insufficient liquidity")
        
        # Update position
        self.positions[position_key] -= amount
        if self.positions[position_key] == 0:
            del self.positions[position_key]
        
        # Update tick data
        self.ticks[lower_tick] -= amount
        self.ticks[upper_tick] += amount
        
        # Update pool liquidity if position is in range
        if lower_tick <= self.tick < upper_tick:
            self.liquidity -= amount
    
    def calculate_amount0(self, lower_tick, upper_tick, liquidity):
        """Calculate amount of token0 for provided liquidity"""
        if upper_tick <= self.tick:
            return 0
        
        lower_sqrt_price = self.get_sqrt_price_at_tick(max(lower_tick, self.tick))
        upper_sqrt_price = self.get_sqrt_price_at_tick(upper_tick)
        
        if lower_sqrt_price == 0 or upper_sqrt_price == 0:
            return 0
            
        amount0 = liquidity * (1 / lower_sqrt_price - 1 / upper_sqrt_price)
        return int(amount0)
    
    def calculate_amount1(self, lower_tick, upper_tick, liquidity):
        """Calculate amount of token1 for provided liquidity"""
        if lower_tick > self.tick:
            return 0
        
        lower_sqrt_price = self.get_sqrt_price_at_tick(lower_tick)
        upper_sqrt_price = self.get_sqrt_price_at_tick(min(upper_tick, self.tick))
        
        amount1 = liquidity * (upper_sqrt_price - lower_sqrt_price)
        return int(amount1)
    
    def cross_tick(self, tick):
        """Handle tick crossing logic"""
        # Find positions affected by this tick
        net_liquidity_change = self.ticks.get(tick, 0)
        
        # Update pool liquidity, with safety check to prevent negative liquidity
        if self.tick < tick:  # Moving up (increasing price)
            self.liquidity += net_liquidity_change
        else:  # Moving down (decreasing price)
            # Prevent liquidity from going negative
            if net_liquidity_change > self.liquidity:
                self.liquidity = 0
            else:
                self.liquidity -= net_liquidity_change
                
        # Ensure liquidity is never negative
        self.liquidity = max(0, self.liquidity)
    
    def swap_simple(self, zero_for_one, amount_specified):
        """
        A simplified swap implementation with less precision
        but better stability for simulation purposes
        
        Args:
            zero_for_one: True if swapping token0 for token1
            amount_specified: Amount to swap
            
        Returns:
            (amount0, amount1): Amounts of tokens exchanged
        """
        if amount_specified <= 0 or self.liquidity <= 0:
            return (0, 0)
        
        # Apply fee
        amount_in = amount_specified * (1 - self.fee)
        
        # Get starting price and convert to human-readable form
        starting_sqrt_price = self.sqrt_price_x96
        starting_price = (starting_sqrt_price / 2**96) ** 2
        
        # If price is too close to zero, limit the impact to prevent going to zero
        if starting_price < 0.1:
            min_price = 0.05  # Set a minimum price floor
            starting_price = max(starting_price, min_price)
            starting_sqrt_price = int(math.sqrt(starting_price) * 2**96)
            self.sqrt_price_x96 = starting_sqrt_price
        
        # Normalize liquidity for price impact calculation
        # This is a key parameter that controls price volatility
        effective_liquidity = max(1000000, self.liquidity / 10**9)
        
        # Calculate price impact factor
        # This creates a more realistic price movement
        impact_factor = amount_in / (effective_liquidity * 100)
        
        # Apply reasonable limits to price movement per swap
        if zero_for_one:  # Selling token0 for token1
            # Limit impact factor to prevent excessive price drop
            impact_factor = min(impact_factor, 0.1)
            
            # New price after swap (decreases)
            new_price = starting_price * (1 - impact_factor)
            # Ensure minimum price
            new_price = max(0.1, new_price)
            
            # Calculate token1 received
            avg_price = (starting_price + new_price) / 2
            token1_out = amount_in * avg_price
            
            # Update pool state
            new_sqrt_price = int(math.sqrt(new_price) * 2**96)
            self.sqrt_price_x96 = max(1, new_sqrt_price)  # Safety check
            
        else:  # Selling token1 for token0
            # Limit impact factor to prevent excessive price increase
            impact_factor = min(impact_factor, 0.1)
            
            # New price after swap (increases)
            new_price = starting_price * (1 + impact_factor)
            
            # Calculate token0 received
            avg_price = (starting_price + new_price) / 2
            token0_out = amount_in / avg_price if avg_price > 0 else 0
            
            # Update pool state
            new_sqrt_price = int(math.sqrt(new_price) * 2**96)
            self.sqrt_price_x96 = new_sqrt_price
        
        # Update tick
        old_tick = self.tick
        self.tick = self.get_tick_at_sqrt_price(self.sqrt_price_x96)
        
        # Check for tick crossings
        if old_tick != self.tick:
            # Find all ticks we've crossed
            if zero_for_one:  # Moving down in price
                sorted_ticks = sorted(self.ticks.keys(), reverse=True)
                for tick in sorted_ticks:
                    if old_tick >= tick > self.tick:
                        self.cross_tick(tick)
            else:  # Moving up in price
                sorted_ticks = sorted(self.ticks.keys())
                for tick in sorted_ticks:
                    if old_tick <= tick < self.tick:
                        self.cross_tick(tick)
        
        if zero_for_one:
            return (amount_specified, -int(token1_out))
        else:
            return (-int(token0_out), amount_specified)
    
    # For backwards compatibility
    swap = swap_simple