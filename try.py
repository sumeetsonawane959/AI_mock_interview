# First, check what models are available
import google.generativeai as genai

# List available models
for m in genai.list_models():
    print(m.name)