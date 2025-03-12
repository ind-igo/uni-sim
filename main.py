from src.simulation import run_basic_simulation
from src.run_simulation import run_comprehensive_simulation

if __name__ == "__main__":
    print("Uniswap V3 Simulation Tool")
    print("===========================")
    print("1. Running basic simulation (simple swaps)")
    run_basic_simulation()
    
    print("\n2. Running comprehensive simulation (multi-agent)")
    # Fewer steps for demonstration purposes
    run_comprehensive_simulation(steps=50)
    
    print("\nAll simulations complete!")