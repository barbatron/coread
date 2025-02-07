from google import genai
import os
import vertexai
from vertexai.generative_models import GenerativeModel

from dotenv import load_dotenv
load_dotenv()

goog_api_key = os.getenv("GOOGLE_GEMINI2_API_KEY")
goog_project_id = os.getenv("GOOGLE_PROJECT_ID")

vertexai.init(project=goog_project_id, location="us-central1")
model = GenerativeModel("gemini-1.5-flash-002")

# Read file from data directory:
with open("data/pfh-exodus.txt", "r") as f:
  book_contents = f.read()
  print(f"Read book contents from file ({len(book_contents.split(" "))} words)")

response = model.generate_content(
    f"Given the book excerpt below, could you describe who the character named Finn is introduced? The book excerpt follows:\n\n{book_contents}"
)

print(response.text)