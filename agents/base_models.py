import google.generativeai as genai
import time

class GeminiModel:
    def __init__(self, api_key, model_name="gemini-2.0-flash-live-001"):
        self.api_key = api_key
        self.model_name = model_name
        self.cache = {}
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def generate(self, prompt, delay=6):
        if prompt in self.cache:
            return self.cache[prompt]
        time.sleep(delay)  # Rate limit management
        output = self.model.generate_content(prompt).text
        self.cache[prompt] = output
        return output
