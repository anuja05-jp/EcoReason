import streamlit as st
import json

from geocode import geocode_location
from live_environment_profile import build_live_environment_profile
from reasoning_engine import build_reasoning_context
from rag_reasoning import attach_evidence
from gemini_reasoner import build_prompt, extract_json, validate_and_correct_result, client, MODEL_NAME
from google.genai import types
from multi_turn_chat import build_chat_system_instruction
import time

MODEL_NAME = "gemini-3.6-flash"
FALLBACK_MODEL_NAME = "gemini-3.5-flash-lite"

class QuotaExhaustedError(Exception):
    pass


def generate_with_retry(prompt, config, max_retries=3):
    models_to_try = [MODEL_NAME, FALLBACK_MODEL_NAME]

    for model_name in models_to_try:
        for attempt in range(1, max_retries + 1):
            try:
                return client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config
                )

            except Exception as e:
                error_text = str(e)

                if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
                    st.warning(
                        f"{model_name} has hit its daily quota — "
                        "switching to fallback model..."
                    )
                    break

                elif "503" in error_text or "UNAVAILABLE" in error_text:
                    if attempt < max_retries:
                        wait = 5 * attempt
                        st.info(
                            f"{model_name} is busy — retrying in {wait}s "
                            f"(attempt {attempt}/{max_retries})..."
                        )
                        time.sleep(wait)
                    else:
                        st.warning(
                            f"{model_name} unavailable after "
                            f"{max_retries} attempts — trying fallback model..."
                        )

                else:
                    raise

    raise QuotaExhaustedError(
        "I've reached the AI service's current request limit across "
        "all available models. Please try again after the quota resets."
    )

st.set_page_config(page_title="EcoReason", page_icon="🌱")
st.title("🌱 EcoReason")
st.caption("AI Biodiversity Intelligence Chatbot — Darukaa.Earth Assessment")


# =========================================================
# SESSION STATE INITIALIZATION
# =========================================================

if "stage" not in st.session_state:
    st.session_state.stage = "ask_location"

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! Tell me where your land is (e.g. 'Jaipur, India') and I'll automatically pull soil, climate, biodiversity, and land-use data for it."}
    ]

if "profile" not in st.session_state:
    st.session_state.profile = None

if "rag_context" not in st.session_state:
    st.session_state.rag_context = None

if "initial_result" not in st.session_state:
    st.session_state.initial_result = None

if "chat_session" not in st.session_state:
    st.session_state.chat_session = None


# =========================================================
# HELPER: FORMAT THE REASONING RESULT AS READABLE MARKDOWN
# =========================================================

def format_result_as_markdown(result):
    if "raw_response" in result:
        return "Sorry, I had trouble generating a clean analysis. Please try again."

    md = f"### Diagnosis\n{result.get('diagnosis', 'Not provided')}\n\n"

    md += "### Key Variables\n"
    for v in result.get("key_variables", []):
        md += f"- {v}\n"

    md += "\n### Causal Chain\n"
    for i, step in enumerate(result.get("causal_chain", []), start=1):
        md += f"{i}. {step}\n"

    md += "\n### Recommendations\n"
    for i, r in enumerate(result.get("recommendations", []), start=1):
        md += f"**{i}. {r.get('action', '')}**\n"
        md += f"- *Why:* {r.get('why', '')}\n"
        md += f"- *Variables involved:* {', '.join(r.get('variables_involved', []))}\n"
        md += f"- *Impacted metrics:* {', '.join(r.get('impacted_metrics', []))}\n"
        md += f"- *Time horizon:* {r.get('time_horizon', '')}\n"
        md += f"- *How to measure:* {r.get('how_to_measure', '')}\n"
        md += f"- *Evidence source:* {r.get('evidence_source', 'None')}\n"
        md += f"- *Confidence:* {r.get('confidence', 'Not provided')}\n\n"


    md += "\n### Uncertainty / Limitations\n"
    for lim in result.get("uncertainty_and_limitations", []):
        md += f"- {lim}\n"

    return md


def format_profile_summary(profile):
    return (
        f"**Location:** {profile['location']} ({profile['coordinates']['lat']}, {profile['coordinates']['lon']})\n\n"
        f"| Category | Value |\n|---|---|\n"
        f"| Soil organic carbon | {profile['soil']['organic_carbon_gkg']} g/kg |\n"
        f"| Soil pH | {profile['soil']['ph']} |\n"
        f"| Avg temperature | {profile['climate']['average_temperature_c']} °C |\n"
        f"| Annual rainfall | {profile['climate']['annual_rainfall_mm']} mm |\n"
        f"| PM2.5 | {profile['pollution']['pm2_5_ug_m3']} µg/m³ |\n"
        f"| Species richness | {profile['biodiversity']['species_richness']} |\n"
        f"| Habitat diversity (Shannon) | {profile['land_cover']['habitat_diversity_shannon']} |\n"
        f"| Tree cover loss | {profile['human_impact']['tree_cover_loss']['total_loss_ha']} ha |\n"
    )


# =========================================================
# RENDER CHAT HISTORY
# =========================================================

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# =========================================================
# HANDLE NEW USER INPUT
# =========================================================

user_input = st.chat_input("Type your response...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

        # ---------------------------------------------------
    # STAGE 1: LOCATION
    # ---------------------------------------------------
    if st.session_state.stage == "ask_location":

        # Check whether the user entered a vague environmental complaint
        vague_indicators = [
            "declining",
            "dying",
            "losing",
            "problem",
            "issue",
            "help",
            "bad",
            "worried",
            "concerned"
        ]

        looks_vague = (
            any(word in user_input.lower() for word in vague_indicators)
            and len(user_input.split()) > 3
        )

        if looks_vague:
            with st.chat_message("assistant"):
                reply = (
                    "I can help with that. To give you a grounded analysis, "
                    "I need a bit more first:\n\n"
                    "1. **Where is your land located?** "
                    "(a city or town name, e.g. 'Jaipur, India')\n"
                    "2. **What are you currently growing or how is the land used?** "
                    "(e.g. 'monoculture wheat', 'mixed cropping', 'pasture')\n\n"
                    "Once I have the location, I'll automatically pull soil, "
                    "climate, and biodiversity data for the area."
                )

                st.markdown(reply)
                st.session_state.messages.append(
                    {"role": "assistant", "content": reply}
                )

        else:
            with st.chat_message("assistant"):
                with st.spinner(
                    f"Fetching live environmental data for {user_input}..."
                ):
                    profile = build_live_environment_profile(user_input)

                if profile is None:
                    reply = (
                        "Sorry, I couldn't find that location — "
                        "try a nearby city or town name."
                    )
                    st.markdown(reply)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": reply}
                    )

                else:
                    st.session_state.profile = profile

                    reply = (
                        "Here's what I found automatically for your area:\n\n"
                        + format_profile_summary(profile)
                    )

                    reply += (
                        "\n\nOne thing I can't get from satellite data — "
                        "what's your specific farming practice or crop? "
                        "(e.g. 'monoculture wheat', 'mixed cropping', "
                        "'pasture' — or type 'skip')"
                    )

                    st.markdown(reply)

                    st.session_state.messages.append(
                        {"role": "assistant", "content": reply}
                    )

                    st.session_state.stage = "ask_farming"
        # ---------------------------------------------------
    # STAGE 2: FARMING PRACTICE -> RUN FULL PIPELINE
    # ---------------------------------------------------
    elif st.session_state.stage == "ask_farming":
        farmer = {
            "soil_organic_carbon": None,
            "rainfall": None,
            "land_use": None,
            "region": None
        }

        if user_input.strip().lower() != "skip":
            farmer["land_use"] = user_input.strip()

        with st.chat_message("assistant"):

            with st.spinner(
                "Running signal detection and retrieving scientific evidence..."
            ):
                reasoning_context = build_reasoning_context(
                    st.session_state.profile,
                    farmer
                )

                rag_context = attach_evidence(reasoning_context)
                st.session_state.rag_context = rag_context

            try:
                with st.spinner("Gemini is reasoning..."):
                    prompt = build_prompt(rag_context)

                    response = generate_with_retry(
                        prompt,
                        types.GenerateContentConfig(
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
                    st.session_state.initial_result = result

                reply = format_result_as_markdown(result)

                st.markdown(reply)
                st.session_state.messages.append(
                    {"role": "assistant", "content": reply}
                )

                system_instruction = build_chat_system_instruction(
                    rag_context,
                    result
                )

                st.session_state.chat_session = client.chats.create(
                    model=MODEL_NAME,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.3
                    )
                )

                followup_prompt = (
                    "\n\nYou can now ask me follow-up questions about this analysis."
                )

                st.markdown(followup_prompt)
                st.session_state.messages.append(
                    {"role": "assistant", "content": followup_prompt}
                )

                st.session_state.stage = "followup"

            except QuotaExhaustedError as e:
                reply = str(e)

                st.error(reply)

                st.session_state.messages.append(
                    {"role": "assistant", "content": reply}
                )

    # ---------------------------------------------------
    # STAGE 3: FOLLOW-UP CONVERSATION
    # ---------------------------------------------------
    elif st.session_state.stage == "followup":
        with st.chat_message("assistant"):
            try:
                with st.spinner("Thinking..."):
                    response = st.session_state.chat_session.send_message(
                        user_input
                    )

                st.markdown(response.text)
                st.session_state.messages.append(
                    {"role": "assistant", "content": response.text}
                )

            except Exception as e:
                error_text = str(e)

                if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
                    reply = (
                        "I've reached the AI service's current request limit. "
                        "Please try again after the quota resets."
                    )

                elif "503" in error_text or "UNAVAILABLE" in error_text:
                    reply = (
                        "The AI service is temporarily overloaded. "
                        "Please try asking again in a moment."
                    )

                else:
                    reply = (
                        "Something went wrong generating a response. "
                        "Please try rephrasing your question."
                    )

                st.error(reply)
                st.session_state.messages.append(
                    {"role": "assistant", "content": reply}
                )


# =========================================================
# SIDEBAR: RESET BUTTON
# =========================================================

with st.sidebar:
    st.header("EcoReason")
    st.caption("Knowledge System: SoilGrids, Open-Meteo, GBIF, ESA WorldCover, OSM, Global Forest Watch")
    if st.button("Start New Analysis"):
        for key in ["stage", "messages", "profile", "rag_context", "initial_result", "chat_session"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()