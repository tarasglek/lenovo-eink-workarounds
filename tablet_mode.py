import pyautogui
import time
import sys # Import sys to exit if images are not found
import datetime # To timestamp the debug screenshot
import logging # Import the logging module

# --- Configure logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout) # Log to console
    ]
)
# --- End logging configuration ---

def save_debug_screenshot_and_exit(failed_image_path):
    """Saves a debug screenshot and exits the script."""
    logging.error(f"Script terminated. Could not find required image: {failed_image_path}")

    # --- Add Debug Screenshot ---
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_screenshot_path = f"debug_screenshot_failure_{timestamp}.png"
    try:
        pyautogui.screenshot(debug_screenshot_path)
        logging.info(f"Saved a debug screenshot: {debug_screenshot_path}. Please examine it to see if the expected image was visible on screen.")
    except Exception as screen_err:
        logging.error(f"Could not save debug screenshot: {screen_err}")
    # --- End Debug Screenshot ---

    sys.exit(1)

def find_and_interact(image_path, action_type='click', max_retries=3, wait_to_disappear=False):
    """
    Finds an image on screen, performs an action, retries if not found,
    and handles errors including saving a debug screenshot and exiting on failure.
    Supports infinite retries if max_retries is float('inf').
    """
    CONFIDENCE_LEVEL = 0.8
    # MAX_RETRIES is now a parameter
    RETRY_DELAY_SECONDS = 1

    initial_location = None
    attempt = 0
    while True: # Loop potentially indefinitely
        try:
            location = pyautogui.locateCenterOnScreen(image_path, confidence=CONFIDENCE_LEVEL)
            if location:
                logging.info(f"Found {image_path} at: {location}")

                initial_location = location # Store the first location

                if action_type == 'click':
                    pyautogui.click(location)
                    logging.info(f"Clicked on {image_path}")
                elif action_type == 'right_click':
                    pyautogui.rightClick(location)
                    logging.info(f"Right-clicked on {image_path}")
                else:
                    logging.info(f"Action '{action_type}' ignored on {image_path} at {location}")
                    if wait_to_disappear:
                        logging.warning(f"wait_to_disappear=True but action_type is '{action_type}'. Disappearance check will be skipped as no action was performed to make it disappear.")
                    return location # Success (image found, no action), return location and exit function

                # --- Start wait_to_disappear logic ---
                if wait_to_disappear:
                    logging.info(f"Waiting for {image_path} to disappear (max_retries for disappearance: {max_retries})...")
                    disappear_attempt = 0
                    while True: 
                        if max_retries != float('inf') and disappear_attempt >= max_retries:
                            logging.error(f"Image {image_path} did not disappear after {disappear_attempt} action re-attempts. Max retries for disappearance reached.")
                            save_debug_screenshot_and_exit(f"{image_path} (failed to disappear after action)")
                            return initial_location # Or None, script exits anyway

                        time.sleep(RETRY_DELAY_SECONDS) # Wait before checking, to give action time to have effect
                        
                        current_location_check = pyautogui.locateCenterOnScreen(image_path, confidence=CONFIDENCE_LEVEL)

                        if current_location_check is None:
                            logging.info(f"{image_path} has disappeared as expected after {disappear_attempt + 1} action(s).")
                            break # Exit disappearance loop, success
                        else:
                            disappear_attempt += 1
                            logging.info(f"Disappearance check attempt {disappear_attempt}{f'/{max_retries}' if max_retries != float('inf') else ''}: {image_path} still visible at {current_location_check}. Re-attempting action '{action_type}'.")
                            
                            # Re-perform the action on the (potentially new) location
                            if action_type == 'click':
                                pyautogui.click(current_location_check)
                                logging.info(f"Clicked again on {image_path} at {current_location_check}")
                            elif action_type == 'right_click':
                                pyautogui.rightClick(current_location_check)
                                logging.info(f"Right-clicked again on {image_path} at {current_location_check}")
                    # End of disappearance loop
                # --- End wait_to_disappear logic ---
                
                return initial_location # Success, return initial_location and exit function

            else:
                 # locateCenterOnScreen raises ImageNotFoundException if None,
                 # but added for robustness in case behavior changes.
                 # Explicitly raise to be caught by the except block below.
                 raise pyautogui.ImageNotFoundException(f"locateCenterOnScreen returned None for {image_path}")

        except pyautogui.ImageNotFoundException:
            attempt += 1
            # Check if we have exceeded retries, but only if max_retries is not infinite
            if max_retries != float('inf') and attempt >= max_retries:
                logging.error(f"Attempt {attempt}/{max_retries}: {image_path} not found. Max retries reached.")
                # Last attempt failed, call the failure handler
                save_debug_screenshot_and_exit(image_path)
                # The line below won't be reached as the helper function exits
                return None # Indicate failure if helper didn't exit

            logging.info(f"Attempt {attempt}{f'/{max_retries}' if max_retries != float('inf') else ''}: {image_path} not found on screen. Retrying {f'indefinitely ' if max_retries == float('inf') else ''}(delay: {RETRY_DELAY_SECONDS}s).")

            time.sleep(RETRY_DELAY_SECONDS)

    # This part should ideally not be reached because the loop either
    # returns on success, exits on failure, or continues indefinitely.
    # Added for logical completeness in case loop condition changes.
    logging.warning(f"Exited retry loop unexpectedly for {image_path}.")
    return None

# --- Main script execution ---
find_and_interact('switch-to-tablet.png', action_type=None, max_retries=float('inf'))
time.sleep(1)  # Wait for the switch to tablet mode to complete 
find_and_interact('switch-to-tablet.png', action_type='click', max_retries=float('inf'))

find_and_interact('windows-logo.png', action_type='click', wait_to_disappear=True)

# Find and right-click the logo
find_and_interact('lenovo.logo.png', action_type='right_click')

# Wait
logging.info("Waiting for 1 second...")
time.sleep(1)

# Find and click the rotate button
find_and_interact('rotate.png', action_type='click')


logging.info("Script completed successfully.")
