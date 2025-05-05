import pyautogui
import time
import sys # Import sys to exit if images are not found

# --- Find and right-click lenovo.logo.png ---
try:
    # Locate the center of the lenovo logo image on the screen.
    # Confidence is added to handle slight variations; adjust if needed.
    lenovo_logo_location = pyautogui.locateCenterOnScreen('lenovo.logo.png', confidence=0.8)

    if lenovo_logo_location is None:
        raise pyautogui.ImageNotFoundException("lenovo.logo.png not found on the screen.")

    print(f"Found lenovo.logo.png at: {lenovo_logo_location}")
    # Move the mouse to the location and right-click
    pyautogui.rightClick(lenovo_logo_location)
    print("Right-clicked on lenovo.logo.png")

except pyautogui.ImageNotFoundException as e:
    print("Error: Image not found during script execution.")
    print(f"Details: {e}") # Print the original exception message separately
    print(f"Image searched for: lenovo.logo.png")
    sys.exit(1) # Exit the script if the first image isn't found

# --- Wait for 1 second ---
print("Waiting for 1 second...")
time.sleep(1)

# --- Find and click rotate.png ---
try:
    # Locate the center of the rotate image on the screen.
    # Confidence is added to handle slight variations; adjust if needed.
    rotate_button_location = pyautogui.locateCenterOnScreen('rotate.png', confidence=0.8)

    if rotate_button_location is None:
        raise pyautogui.ImageNotFoundException("rotate.png not found on the screen after right-click.")

    print(f"Found rotate.png at: {rotate_button_location}")
    # Move the mouse to the location and click
    pyautogui.click(rotate_button_location)
    print("Clicked on rotate.png")

except pyautogui.ImageNotFoundException as e:
    print("Error: Image not found during script execution.")
    print(f"Details: {e}") # Print the original exception message separately
    print(f"Image searched for: rotate.png")
    sys.exit(1) # Exit the script if the second image isn't found

print("Script completed successfully.")
