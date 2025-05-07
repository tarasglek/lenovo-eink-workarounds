import pyautogui
import datetime
import time

print("Starting screenshot capture every 5s. Press Ctrl+C to stop.")
try:
    while True:
        filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        start_time = time.perf_counter()
        pyautogui.screenshot(filename)
        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000
        print(f"Saved: {filename} (took {duration_ms:.2f} ms)")
        time.sleep(5)
except KeyboardInterrupt:
    print("\nScreenshot capture stopped.")
