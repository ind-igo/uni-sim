# Uniswap V3 Simulator

A Python-based simulation tool for testing and visualizing Uniswap V3 pool dynamics with agent-based modeling.

## Overview

This simulator provides a simplified model of Uniswap V3's concentrated liquidity mechanism and allows for testing various market making and trading strategies. The code includes:

1. A simplified Uniswap V3 pool implementation
2. Multiple agent types (market makers, traders, liquidity providers)
3. Simulation framework for running multi-agent scenarios
4. Visualization tools for analyzing results

## Features

- **Uniswap V3 Model**: Implements core mechanisms like concentrated liquidity, tick-based positions, and price range orders
- **Agent Types**:
  - `RandomTrader`: Makes random trades with configurable frequency
  - `TrendFollower`: Follows price trends using a simple momentum strategy
  - `LiquidityProvider`: Passively provides liquidity around the current price
  - `MarketMaker`: Actively manages positions based on volatility and inventory
- **Simulation Framework**: Run configurable simulations with multiple agents interacting
- **Visualization**: Plot price movements, liquidity changes, and trading volume

## Getting Started

### Requirements

- Python 3.10+
- Dependencies: numpy, polars, matplotlib

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   uv pip install -r requirements.txt
   ```

### Running Simulations

Run the basic demo:

```
python main.py
```

This will execute both a basic simulation (simple swaps) and a comprehensive multi-agent simulation.

## Customizing Simulations

You can customize the simulation by modifying:

- Agent parameters in `src/run_simulation.py`
- Pool parameters (fee, tick spacing, initial price)
- Simulation duration and agent composition

## Project Structure

- `src/uniswap_v3_pool.py`: Core pool implementation
- `src/token.py`: Simple token representation
- `src/agent.py`: Trading agent implementations
- `src/simulator.py`: Simulation environment
- `src/simulation.py`: Basic simulation example
- `src/run_simulation.py`: Comprehensive multi-agent simulation

## Extending the Model

The modular design allows for easy extension:

1. Create new agent types by subclassing the `Agent` base class
2. Modify the `swap_simple` method in `UniswapV3Pool` to implement different price impact models
3. Add additional metrics and visualizations to the `Simulator` class

## Limitations

- This is a simplified model for educational and testing purposes
- Does not implement the full Uniswap V3 protocol (e.g., oracle functions, flash loans)
- Price impact calculations are approximated rather than using the exact constant product formula

## License

MIT

## Acknowledgements

This simulator is inspired by the Uniswap V3 protocol but is a simplified implementation for educational purposes.