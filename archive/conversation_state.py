class ConversationState:
    """
    Holds everything we know about the user's land
    across multiple messages in one conversation.
    """

    REQUIRED_FIELDS = [
        "soil_organic_carbon",
        "rainfall",
        "land_use",
        "region"
    ]

    def __init__(self):

        self.fields = {
            field: None
            for field in self.REQUIRED_FIELDS
        }

        # Optional location information
        self.location = None

        # Stores previous messages
        self.conversation_history = []


    def update_field(self, field_name, value):

        if field_name in self.fields:
            self.fields[field_name] = value


    def update_location(self, location):

        self.location = location


    def missing_fields(self):

        return [
            field
            for field, value in self.fields.items()
            if value is None
        ]


    def is_ready(self):

        return len(self.missing_fields()) == 0


    def add_message(self, role, text):

        self.conversation_history.append({
            "role": role,
            "text": text
        })


    def summary(self):

        return {
            "known_fields": self.fields,
            "location": self.location,
            "missing_fields": self.missing_fields(),
            "turns_so_far": len(
                self.conversation_history
            )
        }