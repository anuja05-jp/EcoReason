import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import time

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-3.6-flash"
FALLBACK_MODEL_NAME = "gemini-3.5-flash-lite"

INPUT_PATH = "data/structured/rag_reasoning_context.json"
OUTPUT_PATH = "data/structured/final_recommendation.json"


# =========================================================
# LOAD DATA
# =========================================================

def load_context():
    with open(INPUT_PATH, "r") as f:
        return json.load(f)


# =========================================================
# BUILD PROMPT (same grounding rules as before)
# =========================================================

def build_prompt(context):

    # Flatten all valid evidence source_ids across every interaction,
    # so the validator can check citations against the real pool.
    all_evidence_ids = set()
    interactions_text = []

    for interaction in context.get("multi_variable_interactions", []):
        evidence = interaction.get("scientific_evidence", [])
        for e in evidence:
            all_evidence_ids.add(e["id"])

        evidence_block = "\n\n".join(
            f"  [{e['id']}]\n  {e['text']}" for e in evidence
        ) if evidence else "  (No evidence retrieved for this interaction.)"

        interactions_text.append(
            f"INTERACTION: {interaction['interaction']}\n"
            f"Variables involved: {', '.join(interaction['variables'])}\n"
            f"Reasoning goal: {interaction['reasoning_goal']}\n"
            f"Evidence:\n{evidence_block}"
        )

    interactions_block = "\n\n---\n\n".join(interactions_text) if interactions_text else "(No multi-variable interactions detected.)"

    signals_block = json.dumps(context.get("detected_signals", []), indent=2)
    profile_block = json.dumps(context.get("environmental_profile", {}), indent=2)
    requirements = context.get("reasoning_requirements", {})

    prompt = f"""
You are EcoReason, an AI environmental reasoning assistant.

FULL MEASURED ENVIRONMENTAL PROFILE (some fields may be null — this
means the value could not be measured, NOT that it is zero/absent):

{profile_block}

DETECTED SIGNALS (rule-based flags derived from the profile above):

{signals_block}

MULTI-VARIABLE INTERACTIONS WITH SCIENTIFIC EVIDENCE
(each interaction below is a pre-identified pairing of co-occurring
signals, with evidence retrieved specifically for that pairing):

{interactions_block}

Valid evidence source_id values you may cite: {sorted(all_evidence_ids)}

STRICT RULES — follow exactly:
1. Your causal_chain and recommendations must be built from the
   MULTI-VARIABLE INTERACTIONS above — these are the pre-verified
   variable relationships. Do not introduce a causal link between
   variables that were not paired in an interaction above.
2. Every causal link must be traceable to the evidence text of the
   interaction it comes from. If an interaction has no evidence,
   note it as unverified in uncertainty_and_limitations instead of
   using it in causal_chain.
3. Every "evidence_source" in a recommendation must use a source_id
   from the valid list above. NEVER invent a source_id.
4. NEVER reference a metric whose value in the profile is null.
   Mention missing data explicitly in uncertainty_and_limitations.
5. "uncertainty_and_limitations" must NEVER be empty.
6. Set "confidence" based on evidence strength:
   - High: interactions used have direct, unambiguous evidence
   - Medium: some interactions supported, others weakly
   - Low: fewer than {requirements.get("minimum_variables", 3)} variables have solid evidence support
7. Use at least {requirements.get("minimum_variables", 3)} variables across your reasoning, per reasoning_requirements.
8. Give no more than 3 recommendations, only for evidence-supported interactions.
9. Do not invent scientific studies, percentages, or numbers not present in the evidence or profile.
10. Each recommendation must list at least 3 "variables_involved" and
    at least 3 "impacted_metrics" — this is a multi-metric reasoning
    system, not single-variable advice. Each recommendation must also
    carry its own "evidence_source" (one valid source_id) and its own
    "confidence" rating, since different recommendations can have
    different evidence strength even within the same report.

Return ONLY valid JSON using this exact structure:

{{
  "diagnosis": "Main environmental diagnosis",
  "key_variables": ["variable 1", "variable 2", "variable 3"],
  "causal_chain": ["factor", "effect", "downstream effect"],
  "recommendations": [
    {{
      "action": "Specific action",
      "why": "Why this action addresses the detected interaction",
      "variables_involved": ["variable 1", "variable 2", "variable 3"],
      "impacted_metrics": ["metric 1", "metric 2", "metric 3"],
      "time_horizon": "Short / medium / long term",
      "how_to_measure": "How to monitor progress",
      "evidence_source": "must be one of: {sorted(all_evidence_ids)}",
      "confidence": "High / Medium / Low — confidence for THIS specific recommendation"
    }}
  ],
  "confidence": "High / Medium / Low",
  "uncertainty_and_limitations": [
    "limitation 1 (never leave this list empty)"
  ]
}}
"""
    return prompt


# =========================================================
# GENERATE RESPONSE (this replaces load_model + generate_response)
# =========================================================



def generate_response(context):

    prompt = build_prompt(context)

    print("\nGemini is reasoning...")

    max_retries = 4
    for attempt in range(1, max_retries + 1):
        try:
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
            return response.text.strip()

        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                wait = 5 * attempt  # 5s, 10s, 15s, 20s
                print(f"Gemini temporarily overloaded (attempt {attempt}/{max_retries}). Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise  # a real error, not overload — don't hide it

    raise Exception("Gemini remained unavailable after multiple retries. Try again shortly.")

# =========================================================
# PARSE JSON (unchanged from your version)
# =========================================================

def extract_json(response):
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[len("```json"):]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            print("\nWarning: Gemini did not return perfect JSON.")
            return {"raw_response": response, "parse_error": True}


# =========================================================
# VALIDATE (your code-level safety net, unchanged)
# =========================================================

def validate_and_correct_result(result, context):
    if "raw_response" in result:
        return result

    valid_ids = set()
    for interaction in context.get("multi_variable_interactions", []):
        for e in interaction.get("scientific_evidence", []):
            valid_ids.add(e["id"])

    limitations = result.get("uncertainty_and_limitations", []) or []
    recommendations = result.get("recommendations", [])
    cleaned_recommendations = []

    for rec in recommendations:
        source = rec.get("evidence_source")

        # Drop the evidence citation if it's not a real, retrieved source
        if source not in valid_ids:
            limitations.append(
                f"A recommendation cited an unverifiable source ('{source}') — "
                f"its evidence_source was cleared and confidence lowered."
            )
            rec["evidence_source"] = None
            rec["confidence"] = "Low"

        # Enforce minimum 3 variables/metrics — flag rather than silently pass
        if len(rec.get("variables_involved", [])) < 3:
            limitations.append(
                f"Recommendation '{rec.get('action', '')[:40]}...' involves fewer than "
                f"3 variables — treat as a narrower, single-factor suggestion."
            )

        if len(rec.get("impacted_metrics", [])) < 3:
            limitations.append(
                f"Recommendation '{rec.get('action', '')[:40]}...' lists fewer than "
                f"3 impacted metrics."
            )

        cleaned_recommendations.append(rec)

    result["recommendations"] = cleaned_recommendations

    if not limitations:
        limitations.append(
            "Recommendations are based on point-location data and may not reflect variation across the broader region."
        )

    result["uncertainty_and_limitations"] = limitations
    return result


# =========================================================
# SAVE
# =========================================================

def save_result(result):
    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nFinal recommendation saved to {OUTPUT_PATH}")


# =========================================================
# DISPLAY (unchanged from your version)
# =========================================================

def display_result(result):
    print("\n" + "=" * 70)
    print("ECOREASON AI ENVIRONMENTAL ANALYSIS")
    print("=" * 70)

    if "raw_response" in result:
        print(result["raw_response"])
        return

    print("\nDIAGNOSIS")
    print(result.get("diagnosis", "Not provided"))

    print("\nKEY VARIABLES")
    for variable in result.get("key_variables", []):
        print(f"  • {variable}")

    print("\nCAUSAL CHAIN")
    for i, step in enumerate(result.get("causal_chain", []), start=1):
        print(f"  {i}. {step}")

    print("\nRECOMMENDATIONS")
    for i, r in enumerate(result.get("recommendations", []), start=1):
        print(f"\n  {i}. {r.get('action', '')}")
        print("     Why: " + r.get("why", ""))
        print("     Variables: " + ", ".join(r.get("variables_involved", [])))
        print("     Metrics: " + ", ".join(r.get("impacted_metrics", [])))
        print("     Time horizon: " + r.get("time_horizon", ""))
        print("     Measurement: " + r.get("how_to_measure", ""))
        print("     Evidence source: " + str(r.get("evidence_source", "None")))
        print("     Confidence: " + r.get("confidence", "Not provided"))

    # print("\nSCIENTIFIC BASIS")
    # for evidence in result.get("scientific_basis", []):
    #     print(f"  • {evidence.get('source_id', '')}")
    #     print(f"    {evidence.get('relevance', '')}")

    print("\nCONFIDENCE")
    print(result.get("confidence", "Not provided"))

    print("\nUNCERTAINTY / LIMITATIONS")
    for limitation in result.get("uncertainty_and_limitations", []):
        print(f"  • {limitation}")

    print("\n" + "=" * 70)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    print("Loading EcoReason RAG context...")
    context = load_context()

    response = generate_response(context)
    result = extract_json(response)
    result = validate_and_correct_result(result, context)

    display_result(result)
    save_result(result)