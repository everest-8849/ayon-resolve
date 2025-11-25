import zipfile
import os
import sys

zip_path = r"C:\Users\alexandre.v\AppData\Local\Ynput\AYON\dependency_packages\ayon_2511251215_windows.zip"

print(f"Checking path: {zip_path}")
if not os.path.exists(zip_path):
    print("File does not exist!")
    sys.exit(1)

print("File exists. Attempting to open...")
try:
    with zipfile.ZipFile(zip_path, 'r') as z:
        print(f"Successfully opened {zip_path}")
        found = False
        for name in z.namelist():
            if "opentimelineio" in name and name.endswith(".pyd"):
                print(f"Found binary extension: {name}")
                found = True
        if not found:
            print("No .pyd files found in opentimelineio folder inside zip.")
except Exception as e:
    print(f"Failed to read zip: {e}")
