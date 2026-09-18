from conversation_state import ConversationState
from clarifying_questions import generate_clarifying_question
from extract_fields import extract_fields_from_message


state = ConversationState()


def process_message(message):

    print(f"\nUser: {message}")

    state.add_message(
        "user",
        message
    )

    updates = extract_fields_from_message(
        message,
        state
    )

    for field, value in updates.items():
        state.update_field(
            field,
            value
        )

    print("Extracted:", updates)

    if state.is_ready():

        print(
            "\nSystem: Great, I have everything I need!"
        )

        print(
            "Final state:",
            state.fields
        )

    else:

        question = generate_clarifying_question(
            state.missing_fields()
        )

        print(
            "System:",
            question
        )


# =========================================================
# MULTI-TURN TEST
# =========================================================

print(
    "=== EcoReason Conversation Test ==="
)

process_message(
    "Biodiversity is declining on my land. "
    "My soil has 0.3% organic carbon and "
    "the region is semi-arid."
)

process_message(
    "My rainfall is around 500 mm per year "
    "and I grow wheat as a monoculture."
)


# =========================================================
# VALIDATION
# =========================================================

assert state.fields["soil_organic_carbon"] == 0.3
assert state.fields["rainfall"] == 500.0
assert state.fields["land_use"] == "wheat monoculture"
assert state.fields["region"] == "semi-arid"

assert state.is_ready()

print(
    "\n MULTI-TURN CONVERSATION TEST PASSED"
)