import pyautogui
import time
import sys # Import sys to exit if images are not found
import datetime # To timestamp the debug screenshot

def save_debug_screenshot_and_exit(failed_image_path):
    """Saves a debug screenshot and exits the script."""
    print(f"\nError: Script terminated. Could not find required image: {failed_image_path}")

    # --- Add Debug Screenshot ---
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_screenshot_path = f"debug_screenshot_failure_{timestamp}.png"
    try:
        pyautogui.screenshot(debug_screenshot_path)
        print(f"Saved a debug screenshot: {debug_screenshot_path}")
        print("Please examine this screenshot to see if the expected image was visible on screen.")
    except Exception as screen_err:
        print(f"Could not save debug screenshot: {screen_err}")
    # --- End Debug Screenshot ---

    sys.exit(1)

def find_and_interact(image_path, action_type='click', max_retries=3):
    """
    Finds an image on screen, performs an action, retries if not found,
    and handles errors including saving a debug screenshot and exiting on failure.
    Supports infinite retries if max_retries is float('inf').
    """
    CONFIDENCE_LEVEL = 0.8
    # MAX_RETRIES is now a parameter
    RETRY_DELAY_SECONDS = 1

    attempt = 0
    while True: # Loop potentially indefinitely
        try:
            location = pyautogui.locateCenterOnScreen(image_path, confidence=CONFIDENCE_LEVEL)
            if location:
                print(f"Found {image_path} at: {location}")

                if action_type == 'click':
                    pyautogui.click(location)
                    print(f"Clicked on {image_path}")
                elif action_type == 'right_click':
                    pyautogui.rightClick(location)
                    print(f"Right-clicked on {image_path}")
                else:
                    print(f"Action '{action_type}' performed on {image_path} at {location}")
                    # Add other specific actions if needed

                return location # Success, return location and exit function

            else:
                 # locateCenterOnScreen raises ImageNotFoundException if None,
                 # but added for robustness in case behavior changes.
                 # Explicitly raise to be caught by the except block below.
                 raise pyautogui.ImageNotFoundException(f"locateCenterOnScreen returned None for {image_path}")

        except pyautogui.ImageNotFoundException:
            attempt += 1
            # Check if we have exceeded retries, but only if max_retries is not infinite
            if max_retries != float('inf') and attempt >= max_retries:
                print(f"Attempt {attempt}/{max_retries}: {image_path} not found. Max retries reached.")
                # Last attempt failed, call the failure handler
                save_debug_screenshot_and_exit(image_path)
                # The line below won't be reached as the helper function exits
                return None # Indicate failure if helper didn't exit

            # Print retry message
            if max_retries == float('inf'):
                print(f"Polling {attempt}: {image_path} not found on screen. Retrying indefinitely...")
            else:
                print(f"Attempt {attempt}/{max_retries}: {image_path} not found.")
                print(f"Waiting for {RETRY_DELAY_SECONDS} second(s) before retrying...")

            time.sleep(RETRY_DELAY_SECONDS)

    # This part should ideally not be reached because the loop either
    # returns on success, exits on failure, or continues indefinitely.
    # Added for logical completeness in case loop condition changes.
    print(f"Exited retry loop unexpectedly for {image_path}.")
    return None

# --- Main script execution ---
find_and_interact('switch-to-tablet.png', action_type='click', max_retries=float('inf'))

# Find and right-click the logo
find_and_interact('lenovo.logo.png', action_type='right_click')

# Wait
print("Waiting for 1 second...")
time.sleep(1)

# Find and click the rotate button
find_and_interact('rotate.png', action_type='click')

print("Script completed successfully.")
