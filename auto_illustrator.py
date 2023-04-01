import speech_recognition as sr
import threading
import tkinter as tk
from PIL import ImageTk
import openai
import os, json, time, logging
from stable_horde_client import HordeClient
from auto_1111_client import AutoClient
import argparse


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

# Global variables
all_text = ''
start_time = time.time()

class AutoIllustrator:

    def __init__(self, gpt_key, sd_host, use_horde, horde_api_key, tk_root, tk_label):
        self.tk_root = tk_root
        self.tk_label = tk_label
        self.gpt_model = 'gpt-3.5-turbo'
        self.min_probability_for_gen = 4

        openai.api_key = gpt_key

        # Initialize image ai api client
        self.image_client = HordeClient(horde_api_key) if use_horde else AutoClient(sd_host)

        # Ask for custom style
        default_mod = 'trending on artstation, by Greg Rutkowski, award winning illustration'
        mod_input = input(f'Enter custom image modifiers (default: "{default_mod}")')
        self.modifiers = mod_input if mod_input else default_mod
        
        logging.info('Starting')
        audio_thread = threading.Thread(target=self.start_listen_thread, daemon=True)
        audio_thread.start()

        image_prompt_thread = threading.Thread(target=self.start_prompt_thread, daemon=True)
        image_prompt_thread.start()


    def get_image_prompt_from_gpt(self, recent_text):
        """
        Asks GPT if the recent text is enough to describe a visual image.
        If it is, returns a prompt for generating the image
        """

        try:
            completion = openai.ChatCompletion.create(
                model=self.gpt_model,
                temperature=0.6,
                top_p=1,
                max_tokens=255,
                presence_penalty=0,
                frequency_penalty=0,
                messages=[
                    # {"role": "system", "content": "Your job is to interpret a raw recorded and poorly transcribed conversation. You will determine if the conversation has enough information to visually describe the surroundings. You can write prompts that visually describe the surroundings based on the conversation."},
                    {"role": "user", "content": f"""The following is a raw recorded conversation between several people. Note that there is no punctuation and some of the words may have been transcribed incorrectly.
    Conversation: "{recent_text}"

    Determine if the conversation has enough information to visually describe the surroundings of the people. Disregard unrelated dialog or meaningless words.
    Respond with a json object with a field "probability" which is the probability that this conversation can be used to create a visual image (from 0 to 10). Also include a field "prompt" which is a description of the image that represents what the players are seeing for Dalle2 image generation.
    For the prompt, do not describe the people unless they are specifically talking about themselves. The prompt should be terse, only include visual information, and not try to describe too many things.
    Example:
    {{"probability": 9, "prompt": "An illustration of a huge wolf, red eyes"}}
    Reply with only the json object"""
                    }
                ]
            )

            res = completion.choices[0].message.to_dict()['content']
            start = res.find("{")
            end = res.rfind("}") + 1
            # Extract the json substring
            data_str = res[start:end]
            try:
                data_dict = json.loads(data_str)
                prompt = data_dict['prompt']
                probability = int(data_dict['probability'])
                logging.info(f'Probability: {probability}. Prompt: {prompt}')
                if probability >= self.min_probability_for_gen:
                    return prompt
            except:
                logging.error('Failed to parse ai result', res)

        except Exception as e:
            logging.error(e)


    def prompt_image(self, prompt):
        """
        Takes a prompt and generates an image using the image_client
        """
        prompt += ', ' + self.modifiers
        images = self.image_client.generate_image(prompt)
        for image in images:
            self.display_image(image)

    def display_image(self, image):
        """
        Displays an image in a new window using tk
        """
        if not self.tk_root.winfo_exists():
            print('Window has closed')
            quit()
        if image:
            tk_image = ImageTk.PhotoImage(image)
            self.tk_label.configure(image=tk_image)
            # keep a reference to the image object to avoid garbage collection
            self.tk_label.image = tk_image

    @staticmethod
    def listen_callback(instance, data):
        """
        Handles the audio data that is being listened to
        Uses google to parse the text from the audio
        If it is valid text, it appends the text to the all_text buffer
        """
        global all_text
        try:
            text = instance.recognize_google(data)
            all_text += " " + text
            minutes_so_far = (time.time() - start_time)/60
            num_words = len(all_text.split())
            words_per_minute = num_words / minutes_so_far
            logging.info(f'{text}\nWords per minute: {round(words_per_minute, 1)}')
        except sr.UnknownValueError:
            all_text += '.'
            logging.debug("Google Speech Recognition could not understand audio")
        except sr.RequestError as e:
            logging.error("Could not request results from Google Speech Recognition service; {0}".format(e))

    def start_listen_thread(self):
        """
        Creates an audio source, sets the ambient noise level, starts a thread that listens to audio and calls listen_callback
        """
        r = sr.Recognizer()
        source = sr.Microphone()
        with source as with_source:
            r.adjust_for_ambient_noise(with_source, duration=2)
            r.dynamic_energy_threshold = True
        r.listen_in_background(source, AutoIllustrator.listen_callback, phrase_time_limit=10)
        logging.info('Started audio thread listening')

    def start_prompt_thread(self):
        """
        Main thread that syncronously uses gpt to check if the recent text is a valid image
        If it is, creates and displays the image async in the tk window
        """
        global all_text
        time.sleep(20)
        while True:
            time.sleep(5)
            recent_text = " ".join(all_text.split()[-100:])
            if len(recent_text) > 20:
                logging.info(f'Checking prompt for recent text: {recent_text}')
                prompt = self.get_image_prompt_from_gpt(recent_text)
                if prompt:
                    self.prompt_image(prompt)
                else:
                    time.sleep(15)


if __name__ == '__main__':
    # Parse arguments
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    # Add arguments to the parser
    parser.add_argument("--api-key", type=str, help="The GPT API key to use")
    group.add_argument("--sd-host", type=str, default='', help="The host name of the automatic1111 stable diffusion")
    group.add_argument("--use-horde", type=bool, default=False, help="Whether to use horde mode (instead of automatic1111)")
    group.add_argument("--horde-api-key", type=bool, default='0000000000', help="The horde api key, defaults to the anonymous key")
    # Parse the arguments
    args = parser.parse_args()

    gpt_key = os.getenv('OPENAI_API_KEY')
    if hasattr(args, 'gpt_key'):
        gpt_key = args.gpt_key
    if not gpt_key:
        raise Exception('GPT API key is required ither from --api-key or env var OPENAI_API_KEY')

    # create a root window
    tk_root = tk.Tk()
    # create a label to display the image
    tk_label = tk.Label(tk_root)
    tk_label.pack()

    illustrator = AutoIllustrator(gpt_key, args.sd_host, args.use_horde, args.horde_api_key, tk_root, tk_label)

    tk_root.mainloop()
