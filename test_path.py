from pathlib import Path
import os

BASE_DIR = Path('d:/Sambhav/Understanding AI/smart-traffic')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
print(f"Type: {type(MEDIA_ROOT)}")
print(f"Value: {MEDIA_ROOT}")
