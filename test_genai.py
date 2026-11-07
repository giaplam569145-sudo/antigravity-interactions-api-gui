import inspect
from google import genai

print(inspect.signature(genai.Client().interactions.create))
