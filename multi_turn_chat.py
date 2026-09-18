import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

from hybrid_chat import run_hybrid_chat
from gemini_reasoner import (
    build_prompt, extract_json, validate_and_correct_result,
    display_result, save_result
)

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-3.6-flash"
FALLBACK_MODEL_NAME = "gemini-3.5-flash-lite"


def build_chat_system_instruction(context, initial_result):
    """
    Seeds the ongoing conversation with everything the reasoning
    engine already knows, so follow-up questions stay grounded in
    the SAME evidence and profile, not re-fetched or re-guessed.
    """
    return f"""
You are EcoReason, an AI environmental reasoning assistant having a
follow-up conversation with a farmer/land manager after already
producing an initial analysis.

FULL ENVIRONMENTAL CONTEXT (profile, detected signals, multi-variable
interactions with their scientific evidence):

{json.dumps(context, indent=2)}

YOUR INITIAL ANALYSIS (already delivered to the user):

{json.dumps(initial_result, indent=2)}

RULES FOR FOLLOW-UP ANSWERS:
1. Answer conversationally (plain text, NOT JSON) — this is a
   follow-up chat, not the structured report.
2. Stay grounded in the context and evidence above. If the user asks
   about something not covered by the retrieved evidence or measured
   data, say so honestly rather than inventing an answer.
3. Never state a metric value that isn't in the profile above. If they
   ask about something null (e.g. soil moisture), say it wasn't
   measurable for this location.
4. If the user provides NEW information (e.g. "actually it's mixed
   cropping, not monoculture"), acknowledge that this would change the
   analysis, but note you cannot re-run full signal detection mid-chat
   — recommend starting a new session with the updated info for a
   fully revised report.
5. Keep answers concise and specific — reference the actual numbers
   and evidence sources by name when relevant.
"""


def run_multi_turn_chat(context, initial_result):

    system_instruction = build_chat_system_instruction(context, initial_result)

    chat = client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.3
        )
    )

    print(
        "\nSystem: You can now ask follow-up questions about this "
        "analysis (e.g. 'what about pollution?', 'why not agroforestry?'). "
        "Type 'quit' to end.\n"
    )

    while True:
        user_message = input("You: ").strip()

        if user_message.lower() in ("quit", "exit"):
            print("System: Ending session.")
            break

        if not user_message:
            continue

        response = chat.send_message(user_message)
        print(f"\nEcoReason: {response.text}\n")


if __name__ == "__main__":

    # Run the full pipeline (location → live data → signals → evidence)
    rag_context = run_hybrid_chat()

    if rag_context is None:
        print("Could not build environmental profile. Exiting.")
        exit()

    # Generate the initial structured analysis, same as gemini_reasoner.py
    print("\nGemini is reasoning (initial analysis)...")
    prompt = build_prompt(rag_context)
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=(
                "You are a careful scientific environmental reasoning assistant. "
                "Return ONLY valid JSON. Never include markdown or code fences."
            ),
            temperature=0.2,
            response_mime_type="application/json"
        )
    )

    result = extract_json(response.text.strip())
    result = validate_and_correct_result(result, rag_context)

    display_result(result)
    save_result(result)

    # Now open the follow-up conversation, seeded with everything above
    run_multi_turn_chat(rag_context, result)