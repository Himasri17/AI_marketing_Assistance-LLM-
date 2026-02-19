import requests
from PIL import Image
import io

# create a small test image
img = Image.new('RGB', (224, 224), color=(73, 109, 137))
img_path = 'test_image.jpg'
img.save(img_path, format='JPEG')

files = {'file': open(img_path, 'rb')}
try:
    resp = requests.post('http://127.0.0.1:8001/generate/', files=files, timeout=30)
    print('Status:', resp.status_code)
    print('Response:', resp.text)
except Exception as e:
    print('Request failed:', e)
finally:
    files['file'].close()
