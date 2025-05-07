import datetime
import time

# --- ADD THESE IMPORTS ---
try:
    import win32gui
    import win32ui
    import win32con
    import win32api
    from PIL import Image
    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False
    print("ERROR: pywin32 or Pillow library is not installed. Cannot use pywin32 for screenshots.")
    print("Please install them (e.g., pip install pywin32 Pillow) and try again.")
    # Exit if essential libraries are missing for the core functionality
    import sys
    sys.exit(1)
# --- END ADDED IMPORTS ---


# --- ADD THIS NEW FUNCTION ---
def capture_screen_with_pywin32(filename):
    """
    Captures the entire virtual screen using pywin32 and saves it to a file using Pillow.
    """
    # Get the dimensions of the virtual screen
    left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
    top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
    width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
    height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)

    # Get a handle to the desktop window and its device context (DC)
    hdesktop = win32gui.GetDesktopWindow()
    desktop_dc = win32gui.GetWindowDC(hdesktop)
    img_dc = win32ui.CreateDCFromHandle(desktop_dc)

    # Create a memory DC compatible with the screen DC
    mem_dc = img_dc.CreateCompatibleDC()

    # Create a bitmap object
    screenshot = win32ui.CreateBitmap()
    screenshot.CreateCompatibleBitmap(img_dc, width, height)
    mem_dc.SelectObject(screenshot)

    # Copy the screen into our memory DC
    mem_dc.BitBlt((0, 0), (width, height), img_dc, (left, top), win32con.SRCCOPY)

    # Get the bitmap bits
    bmpinfo = screenshot.GetInfo()
    bmpstr = screenshot.GetBitmapBits(True)

    # Create a Pillow Image from the raw bitmap data
    pil_image = Image.frombuffer(
        'RGB',
        (width, height),
        bmpstr,
        'raw',
        'BGRX',
        0,
        1
    )

    # Save the image
    pil_image.save(filename)

    # Clean up GDI objects
    win32gui.DeleteObject(screenshot.GetHandle())
    mem_dc.DeleteDC()
    img_dc.DeleteDC()
    win32gui.ReleaseDC(hdesktop, desktop_dc)
# --- END NEW FUNCTION ---

print("Starting screenshot capture every 5s (using pywin32). Press Ctrl+C to stop.")
try:
    while True:
        if not PYWIN32_AVAILABLE:
            print("pywin32 or Pillow not available. Stopping.")
            break
            
        filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        start_time = time.perf_counter()
        
        # --- MODIFIED: Call the new screenshot function ---
        try:
            capture_screen_with_pywin32(filename)
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000
            print(f"Saved: {filename} (took {duration_ms:.2f} ms)")
        except Exception as e:
            print(f"Error capturing screenshot with pywin32: {e}")
        # --- END MODIFICATION ---
        
        time.sleep(5)
except KeyboardInterrupt:
    print("\nScreenshot capture stopped.")
