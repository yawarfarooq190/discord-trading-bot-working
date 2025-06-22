import os
import time
import hashlib
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# --- UPDATED IMPORT ---
from trade_parser import parse_trade_signal
from position_calculator import calculate_position_size
from trade_executor import place_order, close_position, check_position_active

# Load environment variables
load_dotenv()

# --- Configuration ---
DISCORD_EMAIL = os.getenv("DISCORD_EMAIL")
DISCORD_PASSWORD = os.getenv("DISCORD_PASSWORD")
DISCORD_CHANNEL_URL = os.getenv("DISCORD_CHANNEL_URL")
RISK_AMOUNT = float(os.getenv("RISK_AMOUNT", "100.0"))

# --- Global State ---
processed_messages = {}
active_trade = None

def login_and_navigate(page):
    """Handles the one-time login and navigation."""
    print("🚀 Starting the login process...")
    try:
        page.goto("https://discord.com/login", wait_until="domcontentloaded")
        page.locator('input[name="email"]').fill(DISCORD_EMAIL)
        page.locator('input[name="password"]').fill(DISCORD_PASSWORD)
        page.locator('button[type="submit"]').click()
        print("\n" + "*"*64)
        print("* IMPORTANT: Please complete any CAPTCHA or 2FA in the browser. *")
        print("*"*64 + "\n")
        page.wait_for_url("https://discord.com/channels/@me", timeout=300000)
        print("✅ Successfully logged into Discord.")
        page.goto(DISCORD_CHANNEL_URL)
        page.wait_for_selector("[id^=message-content-]", timeout=60000)
        print("✅ Channel loaded. Starting to monitor for messages...")
        return True
    except Exception as e:
        print(f"❌ An error occurred during login: {e}")
        return False

def handle_open_signal(trade_data):
    """Calculates position and calls the trade executor to place an order."""
    global active_trade
    if active_trade:
        print(f"  INFO: Ignoring new trade signal, a trade for {active_trade['asset']} is already active.")
        return

    print(f"ACTION: Found new trade to OPEN for {trade_data['asset']}.")
    quantity = calculate_position_size(trade_data['entry'], trade_data['stop_loss'], RISK_AMOUNT)
    
    if quantity:
        order_successful = place_order(
            asset=trade_data['asset'],
            direction=trade_data['direction'],
            quantity=quantity,
            stop_loss=trade_data['stop_loss'],
            take_profit=trade_data.get('take_profit')
        )
        if order_successful:
            active_trade = trade_data
            active_trade['quantity'] = quantity
            print(f"  STATUS: Trade is now ACTIVE. Listening for a close signal.")
        else:
            print(f"  STATUS: Order failed validation or execution. Remaining INACTIVE.")

def handle_close_signal(trade_data):
    """Calls the trade executor to close the active position."""
    global active_trade
    if not active_trade:
        print("  INFO: Ignoring close signal, no trade is active.")
        return
        
    print(f"ACTION: Found signal to CLOSE the active {active_trade['asset']} trade.")
    close_position(asset=active_trade['asset'])
    active_trade = None
    print(f"  STATUS: Trade is now INACTIVE. Listening for a new open signal.")

def monitor_channel(page):
    """Main monitoring loop with a self-correcting position check."""
    global processed_messages, active_trade
    
    print("Performing initial scan to ignore old messages...")
    time.sleep(7)
    initial_html = page.content()
    soup = BeautifulSoup(initial_html, "html.parser")
    for message_li in soup.select("li[class^=messageListItem_]"):
        message_id = message_li.get('id')
        content_div = message_li.select_one("[id^=message-content-]")
        if message_id and content_div:
            initial_text = content_div.get_text(separator="\n", strip=True)
            processed_messages[message_id] = hashlib.md5(initial_text.encode()).hexdigest()
    print(f"✅ Ignored {len(processed_messages)} old messages. Monitoring for NEW messages now.\n")

    while True:
        try:
            # --- NEW: SELF-CORRECTING POSITION CHECK ---
            if active_trade:
                if not check_position_active(active_trade['asset']):
                    print(f"\n--- POSITION CHECK ---")
                    print(f"  INFO: Active trade for {active_trade['asset']} is no longer open on Bybit (SL/TP may have been hit).")
                    active_trade = None
                    print(f"  STATUS: Trade is now INACTIVE. Listening for a new open signal.")
            # --- END OF NEW LOGIC ---

            html_content = page.content()
            soup = BeautifulSoup(html_content, "html.parser")
            for message_li in soup.select("li[class^=messageListItem_]"):
                message_id = message_li.get('id')
                content_div = message_li.select_one("[id^=message-content-]")
                if not message_id or not content_div: continue
                current_text = content_div.get_text(separator="\n", strip=True)
                current_hash = hashlib.md5(current_text.encode()).hexdigest()
                previous_hash = processed_messages.get(message_id)
                if not previous_hash or previous_hash != current_hash:
                    print("\n--- Detected New or Updated Message ---")
                    processed_messages[message_id] = current_hash
                    trade_data = parse_trade_signal(current_text)
                    if trade_data:
                        if trade_data['action'] == 'open': 
                            handle_open_signal(trade_data)
                        elif trade_data['action'] == 'close': 
                            handle_close_signal(trade_data)

            status = f"ACTIVE trade on {active_trade['asset']}" if active_trade else "INACTIVE"
            print(f"Monitoring... Trade Status: {status}. Checking again in 10s.", end="\r")
            time.sleep(10)
        except Exception as e: 
            print(f"\nAn error occurred: {e}")

def main():
    """Main function to run the bot."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        if login_and_navigate(page):
            monitor_channel(page)
        
        print("Script finished. Closing browser.")
        browser.close()

if __name__ == "__main__":
    main()
