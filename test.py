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


@app.route("/", methods=["GET"])
def analyze_character():
    try:
        query = request.args.get("q")
        if not query:
            return jsonify({"error": "Missing query parameter 'q'"}), 400

        # If query begins with a capital letter, assume it's a character or place name
        if query[0].isupper() and query[1].islower():
            book_source = request.args.get("source")
            if not book_source:
                print("Auto-detecting book source...")
                book_source = auto_detect_book_source(query)
            else:
                print(f"Using provided book source: {book_source}")

            # If book_source is not a file, find any file with a name containing book_source as a substring
            if not os.path.exists(f"data/{book_source}"):
                for filename in os.listdir("data"):
                    if book_source in filename:
                        book_source = filename
                        print(f"Auto-selected book source: {book_source}")
                        break

            if book_source:
                with open(f"data/{book_source}", "r") as f:
                    book_contents = f.read()
                # Strip contents beyond the first 3 occurrences of the character name:
                character_occurrences = book_contents.split(query, 3)
                block_lengths = [len(block) for block in character_occurrences]
                print(f"Occurrence block lengths: {block_lengths}")

                all_but_last_blocks_joined = query.join(character_occurrences[:-1])
                print(f"All but last blocks: {len(all_but_last_blocks_joined)}")

                analysis = model.generate_content(
                    f'Given the book excerpt below, provide a brief introduction to who or what "{query}" are? Try to avoid spoilers.\nThe book excerpt follows:\n\n{all_but_last_blocks_joined}'
                )

        else:
            analysis = model.generate_content(
                f'Provide a brief explanation of "{query}".'
            )

        accept_header = request.headers.get("Accept") or "application/json"

        if "application/json" in accept_header:
            return jsonify(
                {
                    "book_source": book_source,
                    "character_name": query,
                    "block_lengths": block_lengths,
                    "analysis": analysis.text,
                }
            )
        elif "text/html" in accept_header:
            return f"<html><body><p>{analysis.text}</p></body></html>"
        return analysis.text

    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
