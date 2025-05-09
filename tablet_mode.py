# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "mouseinfo==0.1.3",
#     "numpy==2.2.5",
#     "opencv-python==4.11.0.86",
#     "pillow==11.2.1",
#     "pyautogui==0.9.54",
#     "pygetwindow==0.0.9",
#     "pymsgbox==1.0.9",
#     "pyperclip==1.9.0",
#     "pyrect==0.2.0",
#     "pyscreeze==1.0.1",
#     "pytweening==1.2.0",
#     "pywin32==310",
# ]
# ///
# add packages with uv add --script tablet_mode.py <package_name>==<version>
# uv run tablet_mode.py
import pyautogui
import time
import sys  # Import sys to exit if images are not found
import datetime  # To timestamp the debug screenshot
import logging  # Import the logging module
import traceback  # For printing error details without recursion
import subprocess  # For running system commands

# --- Add these imports for screen rotation ---
import win32api
import win32con

# --- Add these imports for pygetwindow ---
import pygetwindow as gw

# --- End new imports ---


# Helper function to get screen rotation string
def get_screen_rotation_str():
    try:
        # Get settings for the primary display
        settings = win32api.EnumDisplaySettings(None, win32con.ENUM_CURRENT_SETTINGS)
        orientation_val = settings.DisplayOrientation

        orientation_map = {
            win32con.DMDO_DEFAULT: "0°",  # Landscape
            win32con.DMDO_90: "90°",  # Portrait
            win32con.DMDO_180: "180°",  # Landscape (flipped)
            win32con.DMDO_270: "270°",  # Portrait (flipped)
        }
        # Using short forms for brevity in logs
        return orientation_map.get(orientation_val, f"Unk({orientation_val})")
    except Exception as e:
        # Print error directly to stderr to avoid logging recursion
        print(
            f"ERROR [get_screen_rotation_str]: Error fetching screen rotation: {e}",
            file=sys.stderr,
        )
        traceback.print_exc(file=sys.stderr)  # Print traceback to stderr
        return "RotErr"  # Rotation Error during fetch



# Custom filter to add screen rotation and active window info to log records
class ContextualLogFilter(logging.Filter):  # Renamed
    def filter(self, record):
        record.screen_rotation = get_screen_rotation_str()
        
        # Call the core title getter directly
        title_result = _get_current_active_title_or_marker() # Assumes _get_current_active_title_or_marker is defined
        
        if title_result is _WINDOW_TITLE_ERROR_MARKER:
            record.active_window_display = "WinErr"
        elif title_result is None:
            record.active_window_display = "Win: None"
        else:
            # Truncate long titles for display in logs
            max_title_len = 60 
            display_title = title_result
            if len(display_title) > max_title_len:
                display_title = display_title[:max_title_len-3] + "..."
            record.active_window_display = f"Win: '{display_title}'"
        return True


# --- Configure logging ---
# Create and configure the handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.addFilter(ContextualLogFilter())  # Add our custom (renamed) filter

# Define the new log format including screen_rotation
log_format = "%(asctime)s [%(screen_rotation)s] [%(active_window_display)s] - %(levelname)s - %(message)s"
formatter = logging.Formatter(log_format)
console_handler.setFormatter(formatter)

# Set up basic logging configuration using our custom-configured handler
logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler],  # Pass the list containing our configured handler
)

# --- End logging configuration ---


def save_debug_screenshot_and_exit(failed_image_path):
    """Saves a debug screenshot and exits the script."""
    logging.error(
        f"Script terminated. Could not find required image: {failed_image_path}"
    )

    # --- Add Debug Screenshot ---
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_screenshot_path = f"debug_screenshot_failure_{timestamp}.png"
    try:
        start_time = time.perf_counter()
        pyautogui.screenshot(debug_screenshot_path)
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        logging.info(
            f"Saved a debug screenshot: {debug_screenshot_path} (took {duration_ms:.2f} ms). Please examine it to see if the expected image was visible on screen."
        )
    except Exception as screen_err:
        logging.error(f"Could not save debug screenshot: {screen_err}")
    # --- End Debug Screenshot ---

    sys.exit(1)


def find_and_interact(
    image_path, action_type="click", max_retries=3, wait_to_disappear=False
):
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
    while True:  # Loop potentially indefinitely
        try:
            location = pyautogui.locateCenterOnScreen(
                image_path, confidence=CONFIDENCE_LEVEL
            )
            if location:
                logging.info(f"Found {image_path} at: {location}")

                initial_location = location  # Store the first location

                if action_type == "click":
                    pyautogui.click(location)
                    logging.info(f"Clicked on {image_path}")
                elif action_type == "right_click":
                    pyautogui.rightClick(location)
                    logging.info(f"Right-clicked on {image_path}")
                else:
                    logging.info(
                        f"Action '{action_type}' ignored on {image_path} at {location}"
                    )
                    if wait_to_disappear:
                        logging.warning(
                            f"wait_to_disappear=True but action_type is '{action_type}'. Disappearance check will be skipped as no action was performed to make it disappear."
                        )
                    return location  # Success (image found, no action), return location and exit function

                # --- Start wait_to_disappear logic ---
                if wait_to_disappear:
                    logging.info(
                        f"Waiting for {image_path} to disappear (action will be retried up to {max_retries} times if it doesn't)..."
                    )
                    disappear_retry_count = (
                        0  # Number of times the action has been retried
                    )

                    while True:
                        time.sleep(
                            RETRY_DELAY_SECONDS
                        )  # Wait before checking visibility / after an action

                        try:
                            # Attempt to find the image. If it's gone, pyautogui.locateCenterOnScreen will raise ImageNotFoundException.
                            current_location_check = pyautogui.locateCenterOnScreen(
                                image_path, confidence=CONFIDENCE_LEVEL
                            )

                            # If we are here, the image is STILL VISIBLE.
                            # Check if we have exhausted retries for re-performing the action.
                            if (
                                max_retries != float("inf")
                                and disappear_retry_count >= max_retries
                            ):
                                logging.error(
                                    f"Image {image_path} did not disappear after {disappear_retry_count} re-attempts of action '{action_type}'. Max retries reached."
                                )
                                save_debug_screenshot_and_exit(
                                    f"{image_path} (failed to disappear after {disappear_retry_count} re-attempts of action)"
                                )
                                return initial_location  # Should not be reached due to exit

                            # Image is still visible, and we have retries left (or infinite retries).
                            logging.info(
                                f"Disappearance check: {image_path} still visible at {current_location_check}. Re-attempting action '{action_type}' (re-attempt {disappear_retry_count + 1}{f'/{max_retries}' if max_retries != float('inf') else '/inf'})."
                            )

                            # Re-perform the action on the (potentially new) location
                            if action_type == "click":
                                pyautogui.click(current_location_check)
                                logging.info(
                                    f"Clicked again on {image_path} at {current_location_check}"
                                )
                            elif action_type == "right_click":
                                pyautogui.rightClick(current_location_check)
                                logging.info(
                                    f"Right-clicked again on {image_path} at {current_location_check}"
                                )
                            # Add other action types here if they are supported by wait_to_disappear

                            disappear_retry_count += (
                                1  # Increment the count of re-attempts
                            )

                        except pyautogui.ImageNotFoundException:
                            # SUCCESS: ImageNotFoundException means the image is no longer found.
                            total_actions_performed = (
                                disappear_retry_count + 1
                            )  # Initial action + number of retries
                            logging.info(
                                f"{image_path} has disappeared as expected. Total actions performed: {total_actions_performed}."
                            )
                            break  # Exit disappearance loop, success
                    # End of disappearance while-loop
                # --- End wait_to_disappear logic ---

                return initial_location  # Success, return initial_location and exit function

            else:
                # locateCenterOnScreen raises ImageNotFoundException if None,
                # but added for robustness in case behavior changes.
                # Explicitly raise to be caught by the except block below.
                raise pyautogui.ImageNotFoundException(
                    f"locateCenterOnScreen returned None for {image_path}"
                )

        except pyautogui.ImageNotFoundException:
            attempt += 1
            # Check if we have exceeded retries, but only if max_retries is not infinite
            if max_retries != float("inf") and attempt >= max_retries:
                logging.error(
                    f"Attempt {attempt}/{max_retries}: {image_path} not found. Max retries reached."
                )
                # Last attempt failed, call the failure handler
                save_debug_screenshot_and_exit(image_path)
                # The line below won't be reached as the helper function exits
                return None  # Indicate failure if helper didn't exit

            logging.info(
                f"Attempt {attempt}{f'/{max_retries}' if max_retries != float('inf') else ''}: {image_path} not found on screen. Retrying {f'indefinitely ' if max_retries == float('inf') else ''}(delay: {RETRY_DELAY_SECONDS}s)."
            )

            time.sleep(RETRY_DELAY_SECONDS)

    # This part should ideally not be reached because the loop either
    # returns on success, exits on failure, or continues indefinitely.
    # Added for logical completeness in case loop condition changes.
    logging.warning(f"Exited retry loop unexpectedly for {image_path}.")
    return None


if False:
    # --- Main script execution ---
    find_and_interact(
        "switch-to-tablet.png", action_type=None, max_retries=float("inf")
    )
    time.sleep(1)  # Wait for the switch to tablet mode to complete
    find_and_interact(
        "switch-to-tablet.png", action_type="click", max_retries=float("inf")
    )

    find_and_interact("windows-logo.png", action_type="click", wait_to_disappear=True)

    # Find and right-click the logo
    find_and_interact("lenovo.logo.png", action_type="right_click")

    # Wait
    logging.info("Waiting for 1 second...")
    time.sleep(1)

    # Find and click the rotate button
    find_and_interact("rotate.png", action_type="click")

logging.info("Pressing Ctrl + Windows key + 1...")
pyautogui.hotkey("ctrl", "win", "1")

# Launch High Contrast settings page
logging.info(
    "Launching High Contrast settings page (ms-settings:easeofaccess-highcontrast)..."
)
subprocess.run(
    ["explorer.exe", "ms-settings:easeofaccess-highcontrast"],
    check=False,
    shell=True,
)

# Wait for the Settings window to become active
logging.info("Waiting for 'Settings' window to become active...")
max_wait_time_seconds = 30  # Maximum time to wait for the window
wait_interval_seconds = 0.5  # How often to check

start_loop_time = time.perf_counter()

while True:
    title_result = _get_current_active_title_or_marker() # Assumes this helper is defined

    if isinstance(title_result, str) and "Settings" in title_result:
        logging.info("Target 'Settings' window found and active. Proceeding.")
        break # Successfully found the window

    # Check for timeout
    if (time.perf_counter() - start_loop_time) >= max_wait_time_seconds:
        logging.error(
            f"'Settings' window did not become active within {max_wait_time_seconds} seconds. Timeout."
        )
        # Optionally, call save_debug_screenshot_and_exit here if this is critical
        # save_debug_screenshot_and_exit("Settings_window_timeout_loop")
        sys.exit(1) # Exit due to timeout

    # If not found and not timed out, log concisely and wait
    # The contextual logger will show the current window state.
    logging.info(f"Still waiting for 'Settings'. Retrying in {wait_interval_seconds}s.")
    
    time.sleep(wait_interval_seconds)

# The script continues here if the loop breaks (Settings window found)
# The next line in your script was time.sleep(2)
time.sleep(2)
# Press Tab twice
logging.info("Pressing Tab twice...")
pyautogui.press("tab")
time.sleep(0.1)  # Small delay between key presses if needed
pyautogui.press("tab")

logging.info("Script completed successfully.")
