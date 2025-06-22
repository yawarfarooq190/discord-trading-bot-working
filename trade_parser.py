import re

def parse_trade_signal(message_text: str):
    """
    Parses message text for trading signals.
    This version INTUITIVELY determines trade direction based on Entry vs. Stop Loss prices.
    """
    # --- Pattern 1: Check for a "close" signal (remains the same) ---
    r_booked_pattern = re.compile(r'([+-]?\d+\.?\d*R\s+booked)', re.IGNORECASE)
    r_booked_match = r_booked_pattern.search(message_text)
    if r_booked_match:
        return { "action": "close", "reason": r_booked_match.group(1).strip() }

    # --- Pattern 2: Check for an "open" signal ---
    # The 're.MULTILINE' flag allows '^' to match the start of each line.
    flags = re.IGNORECASE | re.MULTILINE

    # UPDATED: We no longer look for "Long/Short". We just find the asset ticker.
    # The \b ensures we match a whole word (e.g., "ETH" but not "ETHEREUM").
    asset_pattern = re.compile(r'^\s*([A-Z]{3,5})\b', flags)
    
    entry_pattern = re.compile(r'^\s*entry:?\s*\$?\s*([0-9]+\.?\d*)', flags)
    sl_pattern = re.compile(r'^\s*stop[/\s]loss:?\s*\$?\s*([0-9]+\.?\d*)', flags)
    tp_pattern = re.compile(r'^\s*take[/\s]profit:?\s*\$?\s*([0-9]+\.?\d*)', flags)

    asset_match = asset_pattern.search(message_text)
    entry_match = entry_pattern.search(message_text)
    sl_match = sl_pattern.search(message_text)
    tp_match = tp_pattern.search(message_text)

    # An asset, entry, and stoploss are all mandatory for an open signal
    if asset_match and entry_match and sl_match:
        entry_price = float(entry_match.group(1))
        stop_loss_price = float(sl_match.group(1))

        # --- NEW CORE LOGIC: Determine direction from prices ---
        if entry_price == stop_loss_price:
            return None # Invalid signal if prices are the same
        
        direction = "long" if entry_price > stop_loss_price else "short"
        # --- END OF NEW LOGIC ---

        signal_data = {
            "action": "open",
            "asset": asset_match.group(1).upper(),
            "direction": direction, # The direction is now calculated
            "entry": entry_price,
            "stop_loss": stop_loss_price,
            "take_profit": float(tp_match.group(1)) if tp_match else None
        }
        return signal_data

    return None

if __name__ == '__main__':
    print("Testing the parser with price-based direction logic...")

    # Test case where direction should be inferred as "long"
    long_signal = "ETH\nEntry: 2400\nStop Loss: 2350\nTake Profit: 2700"
    
    # Test case from screenshot where direction should be "short"
    short_signal = "ETH\nEntry: $2527\nStop/loss: $2538.85"

    print("\n--- Testing Long Signal (Entry > SL) ---")
    print(f"Parsed: {parse_trade_signal(long_signal)}")

    print("\n--- Testing Short Signal (Entry < SL) ---")
    print(f"Parsed: {parse_trade_signal(short_signal)}")
