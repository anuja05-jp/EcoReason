import json
import torch

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM
)


# =========================================================
# CONFIG
# =========================================================

MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"

INPUT_PATH = (
    "data/structured/rag_reasoning_context.json"
)

OUTPUT_PATH = (
    "data/structured/final_recommendation.json"
)


# =========================================================
# LOAD DATA
# =========================================================

def load_context():

    with open(INPUT_PATH, "r") as f:
        return json.load(f)


# =========================================================
# LOAD QWEN
# =========================================================

def load_model():

    print("\nLoading Qwen...")

    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME
    )

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype="auto",
        device_map="auto"
    )

    print("Qwen loaded successfully.")

    return tokenizer, model


# =========================================================
# BUILD GROUNDED CONTEXT
# =========================================================

def build_grounded_context(context):
    """
    Only pass information that has gone through the
    reasoning/signal-detection pipeline.

    Raw environmental_profile is intentionally NOT passed
    directly to Qwen.
    """

    return {
        "location": context.get("location"),

        "detected_signals": context.get(
            "detected_signals",
            []
        ),

        "multi_variable_interactions": context.get(
            "multi_variable_interactions",
            []
        ),
    }


# =========================================================
# BUILD PROMPT
# =========================================================

def build_prompt(context):

    # -----------------------------------------------------
    # IMPORTANT:
    # Build all Python variables BEFORE starting the
    # f-string prompt.
    # -----------------------------------------------------

    grounded = build_grounded_context(context)

    # Collect variables that actually passed through
    # signal detection / interaction detection.

    available_vars = set()

    for s in grounded["detected_signals"]:

        if isinstance(s, dict) and s.get("type"):

            available_vars.add(
                s["type"]
            )

    for interaction in grounded[
        "multi_variable_interactions"
    ]:

        if not isinstance(interaction, dict):
            continue

        for variable in interaction.get(
            "variables",
            []
        ):

            available_vars.add(
                variable
            )

    available_vars = sorted(
        available_vars
    )

    # -----------------------------------------------------
    # Collect ONLY real evidence IDs
    # -----------------------------------------------------

    evidence_ids = set()

    for interaction in grounded[
        "multi_variable_interactions"
    ]:

        if not isinstance(interaction, dict):
            continue

        for evidence in interaction.get(
            "scientific_evidence",
            []
        ):

            if (
                isinstance(evidence, dict)
                and evidence.get("id")
            ):

                evidence_ids.add(
                    evidence["id"]
                )

    evidence_ids = sorted(
        evidence_ids
    )

    # -----------------------------------------------------
    # PROMPT
    # -----------------------------------------------------

    prompt = f"""
You are EcoReason, an AI environmental reasoning assistant.

Your job is to analyze the environmental system using ONLY:

1. DETECTED SIGNALS
2. MULTI-VARIABLE INTERACTIONS
3. SCIENTIFIC EVIDENCE explicitly attached to those interactions.

Do NOT reason over raw environmental data that did not pass
through the reasoning pipeline.

-------------------------------------------------------
AVAILABLE VARIABLES
-------------------------------------------------------

These are the ONLY variables that are available for reasoning:

{json.dumps(available_vars, indent=2)}

Do not introduce any other variable.

-------------------------------------------------------
AVAILABLE EVIDENCE IDS
-------------------------------------------------------

These are the ONLY scientific evidence IDs available:

{json.dumps(evidence_ids, indent=2) if evidence_ids else "NONE"}

If this says NONE, do not create scientific evidence sources.

-------------------------------------------------------
GROUNDED CONTEXT
-------------------------------------------------------

{json.dumps(grounded, indent=2)}

-------------------------------------------------------
REASONING PROCESS
-------------------------------------------------------

STEP 1 — Identify the main environmental stress.

Use only the detected signals and their supplied values.

STEP 2 — Select the most important variables.

Select 2–3 variables ONLY from AVAILABLE VARIABLES.

Do not use generic labels such as:
- soil
- pollution
- biodiversity
- urbanization
- environmental degradation

unless those exact names appear in AVAILABLE VARIABLES.

Use the actual variable names supplied by the reasoning pipeline.

STEP 3 — Build the causal chain.

Use ONLY variables from AVAILABLE VARIABLES.

The causal chain must be supported by the supplied
multi-variable interactions and scientific evidence.

Do NOT invent causal relationships.

STEP 4 — Generate recommendations.

Each recommendation must directly address a factor
identified in the causal chain.

Do not give generic environmental advice.

STEP 5 — Scientific basis.

Use ONLY scientific evidence whose ID appears in
AVAILABLE EVIDENCE IDS.

NEVER invent:
- studies
- government reports
- researchers
- experts
- papers
- measurements
- datasets
- correlations
- citations
- source IDs

If AVAILABLE EVIDENCE IDS is NONE, return an empty
scientific_basis list.

STEP 6 — State uncertainty.

Clearly identify limitations in the supplied evidence.

-------------------------------------------------------
GROUNDING RULES
-------------------------------------------------------

1. NEVER invent variables.

2. NEVER use a variable that is not present in
   AVAILABLE VARIABLES.

3. Do not use information from raw environmental_profile.

4. If a value is unavailable or null in the supplied
   reasoning context, do not estimate it.

5. Do not calculate correlations unless the supplied
   context contains appropriate historical/time-series data.

6. Do not claim that correlation proves causation.

7. Do not claim that one environmental factor caused another
   unless the supplied interaction/evidence supports that claim.

8. A scientifically plausible relationship is NOT the same
   as an observed relationship.

9. Do not present scientific background knowledge as if it
   were measured evidence from this location.

10. Never invent external sources.

11. Never write phrases such as:
    - "studies show..."
    - "research indicates..."
    - "government reports show..."
    - "experts found..."
    unless that exact evidence exists in the supplied context.

12. Do not describe environmental API data as farmer-reported.

13. Do not describe satellite data as farmer-reported.

14. Do not claim biodiversity is declining unless the supplied
    data contains historical biodiversity measurements showing
    a decline.

15. Do not claim rainfall is increasing or decreasing unless
    the supplied data contains a time series showing that trend.

16. Do not treat a single tree-cover-loss observation as proof
    of biodiversity decline.

17. Recommendations must be connected directly to the
    detected environmental signals.

18. Recommendation metrics should use variables that actually
    exist in AVAILABLE VARIABLES.

19. Do not recommend monitoring a variable that is not available
    unless you explicitly identify it as a proposed future
    measurement rather than existing data.

20. The final reasoning must be internally consistent:

    AVAILABLE VARIABLES
           ↓
    KEY VARIABLES
           ↓
    CAUSAL CHAIN
           ↓
    RECOMMENDATIONS
           ↓
    IMPACTED METRICS

-------------------------------------------------------
CONFIDENCE RULES
-------------------------------------------------------

Use:

High:
Only when the supplied evidence directly supports the
environmental conclusion.

Medium:
When the relationship is scientifically plausible but
the supplied evidence is incomplete.

Low:
When important evidence is missing or the conclusion
is highly uncertain.

Do NOT automatically choose High confidence.

When evidence is incomplete, prefer Medium.

-------------------------------------------------------
UNCERTAINTY RULES
-------------------------------------------------------

Mention important limitations such as:

- unavailable variables
- insufficient historical data
- lack of direct causal evidence
- limited spatial coverage
- limited temporal coverage

Do not invent limitations that are unrelated to the
supplied data.

-------------------------------------------------------
RETURN FORMAT
-------------------------------------------------------

Return ONLY valid JSON.

Do not use markdown.

Do not use ```json.

Do not add explanations outside the JSON.

Use exactly this structure:

{{
  "diagnosis": "Concise main environmental diagnosis",

  "key_variables": [
    "variable 1",
    "variable 2",
    "variable 3"
  ],

  "causal_chain": [
    "Variable A -> Variable B -> Variable C -> environmental consequence"
  ],

  "recommendations": [
    {{
      "action": "Specific intervention",
      "why": "Explain exactly which part of the causal chain this addresses",
      "impacted_metrics": [
        "metric 1",
        "metric 2"
      ],
      "time_horizon": "Short / Medium / Long term",
      "how_to_measure": "Specific monitoring method"
    }},
    {{
      "action": "Specific intervention",
      "why": "Explain exactly which part of the causal chain this addresses",
      "impacted_metrics": [
        "metric 1",
        "metric 2"
      ],
      "time_horizon": "Short / Medium / Long term",
      "how_to_measure": "Specific monitoring method"
    }}
  ],

  "scientific_basis": [
    {{
      "source_id": "Evidence ID from supplied context",
      "relevance": "Explain how this evidence supports the recommendation"
    }}
  ],

  "confidence": "High / Medium / Low",

  "uncertainty_and_limitations": [
    "Important limitation",
    "Important limitation"
  ]
}}

-------------------------------------------------------
FINAL REQUIREMENTS
-------------------------------------------------------

Use exactly 2 recommendations.

Use 2–3 uncertainty/limitation points.

If there are no available scientific evidence IDs,
use:

"scientific_basis": []

Do not fabricate evidence.

Make sure the JSON is completely closed before stopping.
"""

    return prompt


# =========================================================
# GENERATE RESPONSE
# =========================================================

def generate_response(
    tokenizer,
    model,
    context
):

    prompt = build_prompt(
        context
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are a careful scientific environmental "
                "reasoning assistant. "
                "Use ONLY the supplied grounded context. "
                "Never invent variables or evidence. "
                "Return ONLY valid JSON. "
                "Never stop before completing the JSON object."
            )
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(
        text,
        return_tensors="pt"
    ).to(model.device)

    print("\nQwen is reasoning...")

    with torch.no_grad():

        output = model.generate(
            **inputs,
            max_new_tokens=1200,
            do_sample=False
        )

    generated_tokens = output[
        0
    ][
        inputs["input_ids"].shape[1]:
    ]

    response = tokenizer.decode(
        generated_tokens,
        skip_special_tokens=True
    )

    return response.strip()


# =========================================================
# PARSE JSON
# =========================================================

def extract_json(response):

    try:

        return json.loads(
            response
        )

    except json.JSONDecodeError:

        cleaned = response.strip()

        if cleaned.startswith(
            "```json"
        ):

            cleaned = cleaned[
                len("```json"):
            ]

        if cleaned.endswith(
            "```"
        ):

            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        try:

            return json.loads(
                cleaned
            )

        except json.JSONDecodeError:

            print(
                "\nWarning: Qwen did not return "
                "perfect JSON."
            )

            return {
                "raw_response": response,
                "parse_error": True
            }


# =========================================================
# SAVE
# =========================================================

def save_result(result):

    with open(
        OUTPUT_PATH,
        "w"
    ) as f:

        json.dump(
            result,
            f,
            indent=2
        )

    print(
        f"\nFinal recommendation saved to "
        f"{OUTPUT_PATH}"
    )


# =========================================================
# DISPLAY
# =========================================================

def display_result(result):

    print("\n")
    print("=" * 70)
    print(
        "ECOREASON AI ENVIRONMENTAL ANALYSIS"
    )
    print("=" * 70)

    if "raw_response" in result:

        print(
            result["raw_response"]
        )

        return

    print("\nDIAGNOSIS")

    print(
        result.get(
            "diagnosis",
            "Not provided"
        )
    )

    print("\nKEY VARIABLES")

    for variable in result.get(
        "key_variables",
        []
    ):

        print(
            f"  • {variable}"
        )

    print("\nCAUSAL CHAIN")

    for i, step in enumerate(
        result.get(
            "causal_chain",
            []
        ),
        start=1
    ):

        print(
            f"  {i}. {step}"
        )

    print("\nRECOMMENDATIONS")

    for i, recommendation in enumerate(
        result.get(
            "recommendations",
            []
        ),
        start=1
    ):

        print(
            f"\n  {i}. "
            f"{recommendation.get('action', '')}"
        )

        print(
            "     Why: "
            + recommendation.get(
                "why",
                ""
            )
        )

        print(
            "     Metrics: "
            + ", ".join(
                recommendation.get(
                    "impacted_metrics",
                    []
                )
            )
        )

        print(
            "     Time horizon: "
            + recommendation.get(
                "time_horizon",
                ""
            )
        )

        print(
            "     Measurement: "
            + recommendation.get(
                "how_to_measure",
                ""
            )
        )

    print("\nSCIENTIFIC BASIS")

    for evidence in result.get(
        "scientific_basis",
        []
    ):

        print(
            f"  • "
            f"{evidence.get('source_id', '')}"
        )

        print(
            f"    "
            f"{evidence.get('relevance', '')}"
        )

    print("\nCONFIDENCE")

    print(
        result.get(
            "confidence",
            "Not provided"
        )
    )

    print(
        "\nUNCERTAINTY / LIMITATIONS"
    )

    for limitation in result.get(
        "uncertainty_and_limitations",
        []
    ):

        print(
            f"  • {limitation}"
        )

    print(
        "\n" + "=" * 70
    )


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    print(
        "Loading EcoReason RAG context..."
    )

    context = load_context()

    tokenizer, model = load_model()

    response = generate_response(
        tokenizer,
        model,
        context
    )

    result = extract_json(
        response
    )

    display_result(
        result
    )

    save_result(
        result
    )