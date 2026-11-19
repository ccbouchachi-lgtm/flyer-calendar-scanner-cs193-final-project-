
import os
import sys
import json
from pathlib import Path
from google import genai
from datetime import datetime
current_year = datetime.now().year


# 1. Get and validate the image path

if len(sys.argv) != 2:
    raise SystemExit("Usage: python scanner.py <image_path>")

image_path = Path(sys.argv[1]).expanduser()

if not image_path.is_file():
    raise FileNotFoundError(f"Image not found: {image_path}")


# 2. Initialize the Gemini client

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is not configured.")

client = genai.Client(api_key=api_key)


# 3. Define the expected JSON structure

event_schema = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": ["string", "null"]},
                    "organizer": {"type": ["string", "null"]},
                    "date": {"type": ["string", "null"]},
                    "start_time": {"type": ["string", "null"]},
                    "end_time": {"type": ["string", "null"]},
                    "location": {"type": ["string", "null"]}
                },
                "required": [
                    "title",
                    "organizer",
                    "date",
                    "start_time",
                    "end_time",
                    "location"
                ]
            }
        }
    },
    "required": ["events"]
}


# 4. Define Gemini's instructions

system_instruction = f"""
You are an event information extraction assistant.

1. Extract only information explicitly visible or clearly stated in the flyer.
2. Never invent, assume, or guess missing information, except for the year as specified below.
3. If a field is missing or unclear, return null.
4. Preserve the original event title and organization name.
5. Always return dates in YYYY-MM-DD format.
   If the flyer specifies a year, use that year.
   If the flyer does not specify a year, use {current_year}.
   Never invent a missing month or day.
6. Use HH:MM for times.
7. Distinguish start time from end time.
8. Include the venue, building, room, or address.
9. Extract multiple events separately.
10. Return no promotional descriptions or unrelated information.

Return the information using the provided JSON schema.
"""


# 5. Upload the image to Google's File API

print("Uploading flyer...")

uploaded_file = client.files.upload(file=str(image_path))


# 6. Send the image to Gemini

print("Extracting event information...")

interaction = client.interactions.create(
    model="models/gemini-4-hydrogen",
    input=[
        {
            "type": "text",
            "text": "Extract the event information from this flyer."
        },
        {
            "type": "image",
            "uri": uploaded_file.uri,
            "mime_type": uploaded_file.mime_type
        }
    ],
    system_instruction=system_instruction,
    response_format={
        "type": "text",
        "mime_type": "application/json",
        "schema": event_schema
    }
)


# 7. Convert Gemini's JSON response into Python data

result = json.loads(interaction.output_text)


# 8. Save the result to a JSON file

output_folder = Path("output")
output_folder.mkdir(exist_ok=True)

output_file = output_folder / "events.json"

with open(output_file, "w", encoding="utf-8") as file:
    json.dump(result, file, indent=4, ensure_ascii=False)


print(f"Extraction complete! Saved to {output_file}")
