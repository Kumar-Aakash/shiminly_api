import openai
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

class FlashcardRequest(BaseModel):
    content: str
    num_flashcards: int

def generate_flashcards(content: str, num_flashcards: int):
    """
    Generate flashcards from the given content.
    """
    prompt = (
        f"Create {num_flashcards} concise and informative flashcards based on the following content. "
        f"Each flashcard should have a heading and a short description (4-5 lines)."
        f"\n\nContent:\n{content}\n\nFlashcards:"
    )

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=900,
            temperature=0.7
        )
        flashcards_text = response.choices[0].message['content'].strip()
        return flashcards_text
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-flashcards")
async def generate_flashcards_endpoint(request: FlashcardRequest):
    """
    Endpoint to generate flashcards based on the given content and number of cards.
    """
    flashcards_text = generate_flashcards(request.content, request.num_flashcards)
    flashcards = []
    current_heading = ""
    current_description = ""

    import re
    lines = flashcards_text.split("\n")

    for line in lines:
        line = line.strip()
        if re.match(r"^Flashcard\s+\d+:$", line):
            if current_heading or current_description:
                flashcards.append({
                    "heading": current_heading.strip(),
                    "description": current_description.strip()
                })
                current_heading, current_description = "", ""
        elif line.lower().startswith("heading:"):
            current_heading = line.replace("Heading:", "").strip()
        elif line.lower().startswith("description:"):
            current_description = line.replace("Description:", "").strip()
        elif line:
            current_description += f" {line}"

    if current_heading or current_description:
        flashcards.append({
            "heading": current_heading.strip(),
            "description": current_description.strip()
        })

    if not flashcards:
        return {"error": "No valid flashcards could be generated. Please check the input content or OpenAI response."}

    return {"flashcards": flashcards}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
