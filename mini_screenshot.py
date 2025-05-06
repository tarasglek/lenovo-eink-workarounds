import pyautogui
import datetime

filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
pyautogui.screenshot(filename)
print(f"Saved single screenshot: {filename}")
