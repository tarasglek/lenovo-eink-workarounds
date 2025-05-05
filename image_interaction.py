import pyautogui
import time
import sys # Import sys to exit if images are not found

def find_and_interact(image_path, action_type='click', confidence=0.8):
    """Finds an image on screen, performs an action, and handles not found errors."""
    location = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
    if location is None:
        # Raise the specific exception type pyautogui uses internally
        raise pyautogui.ImageNotFoundException(f"{image_path} not found on the screen.")

    print(f"Found {image_path} at: {location}")

    if action_type == 'click':
        pyautogui.click(location)
        print(f"Clicked on {image_path}")
    elif action_type == 'right_click':
        pyautogui.rightClick(location)
        print(f"Right-clicked on {image_path}")
    else:
        # Optional: Handle unknown action types if needed, or just ignore
        print(f"Action '{action_type}' performed on {image_path} at {location}")
        # If you need specific actions beyond click/right_click, add them here.
        # For now, we assume pyautogui handles other action strings if they exist,
        # or you might want to raise an error for unsupported actions.

    return location # Return location in case it's needed later

# --- Main script execution ---
try:
    # Find and right-click the logo
    find_and_interact('lenovo.logo.png', action_type='right_click', confidence=0.8)

    # Wait
    print("Waiting for 1 second...")
    time.sleep(1)

    # Find and click the rotate button
    find_and_interact('rotate.png', action_type='click', confidence=0.8)

    print("Script completed successfully.")

except pyautogui.ImageNotFoundException as e:
    # Centralized error handling for image not found
    print(f"\nError: Script terminated. Could not find required image.")
    print(f"Details: {e}")
    sys.exit(1)
except Exception as e:
    # Catch any other unexpected errors during execution
    print(f"\nAn unexpected error occurred: {e}")
    sys.exit(1)
