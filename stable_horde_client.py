import requests
from typing import List
import time
from PIL import Image
import io, base64
import logging

class HordeClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://stablehorde.net/api/v2"
        # List of models that can be used
        preferred_models = ['stable_diffusion', 'Midjourney Diffusion', 'Darkest Diffusion']
        # 2.1 doesn't work unless you have account
        # preferred_models = ['stable_diffusion_2.1']
        self.models = self.get_models(preferred_models)
        if len(self.models) > 1:
            models_str = '\n'.join(f'{i}: {m}' for i, m in enumerate(self.models))
            choice = input(f"Choose a model:\n{models_str}\n")
            self.model = self.models[int(choice)]
    
    def get_models(self, preferred_models) -> List[str]:
        models_url = f"{self.base_url}/status/models?type=image"
        response = requests.get(models_url, headers={'apikey': self.api_key})
        models = response.json()
        res = []
        for m in models:
            if m['name'] in preferred_models:
                res.append(m['name'])
        if len(res) == 0:
            raise Exception('No preferred models found')
        return res
    
    def generate_image(self, prompt: str) -> str:
        generate_url = f"{self.base_url}/generate/async"
        data = {
            "prompt": prompt,
            "params": {
                "sampler_name": "k_euler_a",
                "toggles": [
                1,
                4
                ],
                "cfg_scale": 7,
                "height": 512, #768 if self.hi_res else 512,
                "width": 512, #768 if self.hi_res else 512,
                "steps": 18,
                "n": 1
            },
            "nsfw": False,
            "trusted_workers": False,
            "slow_workers": True,
            "censor_nsfw": True,
            # "workers": [
            #     "string"
            # ],
            "models": self.models,
            "r2": False,
            # "shared": false,
            # "replacement_filter": true
        }
        response = requests.post(generate_url, headers={'apikey': self.api_key}, json=data)
        try:
            uuid = response.json()["id"]
        except:
            logging.error(f'Failed to parse response {response.json()}')
        counter = 0
        while counter < 120:
            time.sleep(1)
            is_complete = self.check_generation(uuid)
            if is_complete:
                images = self.get_generated_image(uuid)
                return images
            counter += 1
    
    def check_generation(self, uuid: str) -> bool:
        check_url = f"{self.base_url}/generate/check/{uuid}"
        response = requests.get(check_url, headers={'apikey': self.api_key})
        res = response.json()
        is_complete = res["done"]
        return is_complete
    
    def get_generated_image(self, uuid: str) -> str:
        status_url = f"{self.base_url}/generate/status/{uuid}"
        response = requests.get(status_url, headers={'apikey': self.api_key})
        res = response.json()
        images = []
        for gen in res['generations']:
            image = Image.open(io.BytesIO(base64.b64decode(gen['img'])))
            images.append(image)
        return images
