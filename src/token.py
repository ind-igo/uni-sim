class Token:
    def __init__(self, name, symbol, decimals):
        """
        Initialize a token
        
        Args:
            name: Token name
            symbol: Token symbol
            decimals: Token decimals
        """
        self.name = name
        self.symbol = symbol
        self.decimals = decimals
    
    def __str__(self):
        return f"{self.symbol}"
    
    def format_amount(self, amount):
        """Format token amount with decimals"""
        return amount / (10 ** self.decimals)