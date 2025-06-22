# This file will not be run directly.
# It will be imported by our main script to perform calculations.

def calculate_position_size(entry_price: float, stop_loss_price: float, risk_amount: float):
    """
    Calculates the position size (quantity) based on the risk amount.

    The formula is: quantity = risk_amount / |entry_price - stop_loss_price|

    This tells you how many units of the asset (e.g., how much BTC) to buy or sell
    so that if the trade hits your stop loss, you lose exactly your desired risk amount.

    Args:
        entry_price (float): The price at which the trade is entered.
        stop_loss_price (float): The price at which to exit if the trade fails.
        risk_amount (float): The fixed amount of money you are willing to risk (e.g., 100.0 for $100).

    Returns:
        float: The calculated quantity of the asset to trade, or None if prices are the same.
    """
    # The difference between entry and stop loss is the risk per unit of the asset.
    price_difference = entry_price - stop_loss_price

    # We must ensure the difference is not zero to avoid division by zero error.
    if price_difference == 0:
        print("⚠️ Warning: Entry price and Stop Loss are the same. Cannot calculate position size.")
        return None

    # We use abs() to get the absolute difference, making it always positive.
    # This works for both LONG (entry > sl) and SHORT (entry < sl) trades.
    quantity = risk_amount / abs(price_difference)

    return quantity

if __name__ == '__main__':
    # This block allows us to test the function directly if we run `python position_calculator.py`
    print("Testing the Position Calculator...")

    # --- Test Case 1: A standard LONG position ---
    my_risk = 100.0  # Risking $100
    long_entry = 50000.0
    long_sl = 49500.0
    
    print(f"\n--- LONG Trade Example ---")
    print(f"Risking ${my_risk} on a trade from {long_entry} to {long_sl}")
    long_quantity = calculate_position_size(long_entry, long_sl, my_risk)
    
    # We round the quantity for readability. Exchanges have specific rules for precision.
    if long_quantity is not None:
        print(f"Calculated Position Size (Quantity): {long_quantity:.4f}")
        print(f"Meaning: You should buy {long_quantity:.4f} units of the asset.")
        # Verification: 0.2 units * ($50000 - $49500) price diff = 0.2 * $500 = $100 loss. Correct.

    # --- Test Case 2: A standard SHORT position ---
    short_entry = 60000.0
    short_sl = 61000.0

    print(f"\n--- SHORT Trade Example ---")
    print(f"Risking ${my_risk} on a trade from {short_entry} with SL at {short_sl}")
    short_quantity = calculate_position_size(short_entry, short_sl, my_risk)

    if short_quantity is not None:
        print(f"Calculated Position Size (Quantity): {short_quantity:.4f}")
        print(f"Meaning: You should sell {short_quantity:.4f} units of the asset.")
        # Verification: 0.1 units * |$60000 - $61000| price diff = 0.1 * $1000 = $100 loss. Correct.
