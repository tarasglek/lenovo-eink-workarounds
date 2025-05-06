import pyautogui
import time
import datetime

print("Starting screenshot capture every 5s. Press Ctrl+C to stop.")
try:
    while True:
        filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        pyautogui.screenshot(filename)
        print(f"Saved: {filename}")
        time.sleep(5)
except KeyboardInterrupt:
    print("\nScreenshot capture stopped.")
