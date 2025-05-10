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
# alternatives: https://github.com/pywinauto/pywinauto/
# https://pypi.org/project/pyuiauto/
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

_WINDOW_TITLE_ERROR_MARKER = object()  # Unique marker for title fetching errors


def wait_for_window_title(
    target_title_substring,
    max_wait_seconds=30,
    interval_seconds=1,
    exit_on_timeout=True,
):
    """
    Waits for a window containing the target_title_substring to become active.

    Args:
        target_title_substring (str): The substring to look for in the active window's title.
        max_wait_seconds (int): Maximum time in seconds to wait for the window.
        interval_seconds (float): How often in seconds to check for the window.
        exit_on_timeout (bool): If True, calls save_debug_screenshot_and_exit on timeout.

    Returns:
        str: The full title of the active window if found.
        None: If timeout occurs and exit_on_timeout is False.
              (If exit_on_timeout is True, the script will exit instead of returning None).
    """
    logging.info(
        f"Waiting for window with title containing: '{target_title_substring}'..."
    )
    start_time = time.perf_counter()

    while True:
        current_title = _get_current_active_title_or_marker()

        if isinstance(current_title, str) and target_title_substring in current_title:
            logging.info(
                f"Target window '{current_title}' (containing '{target_title_substring}') found and active."
            )
            return current_title  # Success

        elapsed_time = time.perf_counter() - start_time
        if elapsed_time >= max_wait_seconds:
            logging.error(
                f"Timeout: Window with title substring '{target_title_substring}' did not become active within {max_wait_seconds} seconds."
            )
            if exit_on_timeout:
                # Sanitize substring for filename
                safe_substring = "".join(
                    c if c.isalnum() else "_" for c in target_title_substring
                )
                save_debug_screenshot_and_exit(
                    f"Timeout_waiting_for_window_{safe_substring[:30]}"
                )  # Pass a descriptive message
            return None  # Timeout

        # Log concisely; the contextual logger will show the current window state if any.
        logging.info(
            f"Still waiting for '{target_title_substring}'. Retrying in {interval_seconds}s."
        )
        time.sleep(interval_seconds)


def _get_current_active_title_or_marker():
    """
    Attempts to get the title of the currently active window.
    Returns:
        - The title string if a window is active.
        - None if no window is currently active.
        - _WINDOW_TITLE_ERROR_MARKER if an exception occurs during fetching.
    """
    try:
        active_window = gw.getActiveWindow()
        if active_window:
            return active_window.title
        return None  # No active window
    except Exception as e:
        # Print error directly to stderr to avoid logging recursion if this
        # function is called by the logger context filter.
        print(
            f"ERROR [_get_current_active_title_or_marker]: Error fetching active window: {e}",
            file=sys.stderr,
        )
        traceback.print_exc(file=sys.stderr)
        return _WINDOW_TITLE_ERROR_MARKER


def press_with_pause(key_or_keys, pause_seconds=0.1):
    """
    Presses a key (or a combination of keys) and then pauses.

    Args:
        key_or_keys: A string for a single key, or a list/tuple of strings for a hotkey combination.
        pause_seconds (float): Duration to pause after the key press. Defaults to 0.1.
    """
    action_description = ""
    if isinstance(key_or_keys, (list, tuple)):
        action_description = f"hotkey: {', '.join(key_or_keys)}"
        pyautogui.hotkey(*key_or_keys)
    else:
        action_description = f"key: '{key_or_keys}'"
        pyautogui.press(key_or_keys)

    logging.info(f"Pressed {action_description} and pausing for {pause_seconds}s.")
    if pause_seconds > 0:
        time.sleep(pause_seconds)


# Helper function to get screen rotation string
def get_screen_rotation():
    try:
        # Get settings for the primary display
        settings = win32api.EnumDisplaySettings(None, win32con.ENUM_CURRENT_SETTINGS)
        orientation_val = settings.DisplayOrientation

        orientation_map = {
            win32con.DMDO_DEFAULT: 0,  # Landscape
            win32con.DMDO_90: 90,  # Portrait
            win32con.DMDO_180: 180,  # Landscape (flipped)
            win32con.DMDO_270: 270,  # Portrait (flipped)
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
        return -1  # Rotation Error during fetch


# Custom filter to add screen rotation and active window info to log records
class ContextualLogFilter(logging.Filter):  # Renamed
    def filter(self, record):
        record.screen_rotation = get_screen_rotation()

        # Call the core title getter directly
        title_result = (
            _get_current_active_title_or_marker()
        )  # Assumes _get_current_active_title_or_marker is defined

        if title_result is _WINDOW_TITLE_ERROR_MARKER:
            record.active_window_display = "WinErr"
        elif title_result is None:
            record.active_window_display = "Win: None"
        else:
            record.active_window_display = f"Win: '{title_result}'"
        return True


# --- Configure logging ---
# Create and configure the handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.addFilter(ContextualLogFilter())  # Add our custom (renamed) filter

# Define the new log format including screen_rotation
log_format = "%(asctime)s [%(screen_rotation)d] [%(active_window_display)s] - %(levelname)s - %(message)s"
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
    image_path,
    action_type="click",
    max_retries=3,
    wait_to_disappear=False,
    exit_on_timeout=True,
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

        except pyautogui.ImageNotFoundException:
            attempt += 1
            # Check if we have exceeded retries, but only if max_retries is not infinite
            if max_retries != float("inf") and attempt >= max_retries:
                logging.error(
                    f"Attempt {attempt}/{max_retries}: {image_path} not found. Max retries reached."
                )
                if exit_on_timeout:
                    # Last attempt failed, call the failure handler
                    save_debug_screenshot_and_exit(image_path)
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


if True:
    # --- Main script execution ---
    active_settings_window_title = wait_for_window_title("ThinkbookEinkPlus")
    time.sleep(4)  # Wait for the switch to tablet mode to complete
    find_and_interact(
        "switch-to-tablet.png", action_type="click", max_retries=float("inf")
    )

    # if screen orientation != 90
    if get_screen_rotation() != 90:
        logging.info("Screen rotation is not 90 degrees. Attempting to rotate...")
        # Find and right-click the logo
        find_and_interact("lenovo.logo.png", action_type="right_click")

        time.sleep(1)
        # Find and click the relevant rotate button
        find_and_interact("rotate.png", action_type="click")

    find_and_interact("windows-logo.png", action_type="click", wait_to_disappear=True)


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
active_settings_window_title = wait_for_window_title("Settings")
# If the function returns, the window was found (due to default exit_on_timeout=True).
# The script will have exited via save_debug_screenshot_and_exit if the window wasn't found in time.

# The script continues here if the window was found
# The next line in your script was time.sleep(2)
time.sleep(4)
# Press Tab twice
logging.info("Starting to select eink theme...Pressing Tab twice...")
press_with_pause("tab", pause_seconds=0.1)  # First tab with pause
pyautogui.press("tab")  # Second tab (original had no sleep after this specific press)
for _ in range(5):
    press_with_pause("down", pause_seconds=0.1)
# tab, then enter
logging.info("Pressing Tab, then Enter...")
press_with_pause("tab", pause_seconds=0.1)  # Tab with pause
pyautogui.press("enter")  # Enter (original had no sleep after this specific press)

active_settings_window_title = wait_for_window_title(
    "Settings", max_wait_seconds=30, interval_seconds=0.5
)

# press alt + f4 to close the settings window
logging.info("Pressing Alt + F4 to close the Settings window...")
pyautogui.hotkey("alt", "f4")
logging.info("Script completed successfully.")
