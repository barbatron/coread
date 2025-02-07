import os
from dotenv import load_dotenv

from google import genai
import vertexai
from vertexai.generative_models import GenerativeModel

from flask import Flask, request, jsonify

load_dotenv()

# Suppress logging warnings
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"

goog_api_key = os.getenv("GOOGLE_GEMINI2_API_KEY")
goog_project_id = os.getenv("GOOGLE_PROJECT_ID")

vertexai.init(project=goog_project_id, location="us-central1")
model = GenerativeModel("gemini-1.5-flash-002")


def auto_detect_book_source(character_name):
    # Scan through text files in data directory to find character name
    book_with_most_occurrences = None
    occurrence_count = None
    for filename in os.listdir("data"):
        with open(f"data/{filename}", "r") as f:
            book_contents = f.read()
            occurrences = book_contents.count(character_name)
            if occurrences > 0:
                if book_with_most_occurrences is None or occurrences > occurrence_count:
                    book_with_most_occurrences = filename
                    occurrence_count = occurrences
    print(
        f"Detected book source for {character_name}: {book_with_most_occurrences} with {occurrence_count} occurrences"
    )
    return book_with_most_occurrences


app = Flask(__name__)


@app.route("/analyze-character", methods=["GET"])
def analyze_character(filename):
    try:
        character_name = request.args.get("q")
        if not character_name:
            return jsonify({"error": "Missing character parameter"}), 400

        book_source = request.args.get("source")
        if not book_source:
            book_source = auto_detect_book_source(character_name)

        with open(f"data/{book_source}", "r") as f:
            book_contents = f.read()

        # Strip contents beyond the first 3 occurrences of the character name:
        character_occurrences = book_contents.split(character_name, 3)
        block_lengths = [len(block) for block in character_occurrences]
        print(f"Occurrence block lengths: {block_lengths}")

        # response = model.generate_content(
        #     f"Given the book excerpt below, could you describe who the character named {character_name} is introduced? The book excerpt follows:\n\n{book_contents}"
        # )

        return jsonify(
            {
                "book_source": book_source,
                "character_name": character_name,
                "block_lengths": block_lengths,
                "analysis": "(disabled)",
            }
        )

    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
