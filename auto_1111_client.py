import requests
from PIL import Image
import io, base64

class AutoClient:
    def __init__(self, host):
        self.url = f"http://{host}:7860/sdapi/v1/txt2img"
        

    def generate_image(self, prompt: str) -> str:
        response = requests.post(url=self.url, json={'prompt': prompt,'sampler_index': 'Euler', 'steps': 18})
        try:
            data = response.json()
            if data and 'images' in data:
                images = [Image.open(io.BytesIO(base64.b64decode(i.split(',', 1)[0]))) for i in data['images']]
                return images
        except:
            return []