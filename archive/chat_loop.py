from conversation_state import ConversationState
from clarifying_questions import generate_clarifying_question
from extract_fields import extract_fields_from_message

state = ConversationState()

print("System: Hi! Tell me about your land and I'll help identify biodiversity improvements.\n")

while not state.is_ready():
    user_input = input("You: ")
    state.add_message("user", user_input)

    # Try to fill in any missing fields from what they just said
    updates = extract_fields_from_message(user_input, state)
    for field, value in updates.items():

        if field == "location":
            state.update_location(value)
        else:
            state.update_field(field, value)

    if state.is_ready():
        print("\nSystem: Great, I have everything I need!")
        print("Collected info:")
        print("Location:", state.location)
        print("Environmental fields:", state.fields)
        break

    question = generate_clarifying_question(state.missing_fields())
    state.add_message("system", question)
    print(f"System: {question}\n")