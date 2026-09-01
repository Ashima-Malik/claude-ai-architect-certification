import json
import anthropic


# ============================================================
# STEP 1: Create the Claude client
# ============================================================

# Anthropic reads the API key from the ANTHROPIC_API_KEY
# environment variable.

client = anthropic.Anthropic()


# ============================================================
# STEP 2: Define the TOOL for Claude
# ============================================================

# IMPORTANT:
#
# This is NOT the actual Python function.
#
# This tells Claude:
#
# "You have access to a tool called create_calendar_event.
#  If you decide to use it, here are the arguments you
#  should provide."

tools = [
    {
        "name": "create_calendar_event",

        "description": (
            "Create a calendar event with attendees "
            "and optional recurrence."
        ),

        "input_schema": {
            "type": "object",

            "properties": {

                # -----------------------------
                # Event title
                # -----------------------------

                "title": {
                    "type": "string"
                },

                # -----------------------------
                # Event start time
                # -----------------------------

                "start": {
                    "type": "string",
                    "format": "date-time"
                },

                # -----------------------------
                # Event end time
                # -----------------------------

                "end": {
                    "type": "string",
                    "format": "date-time"
                },

                # -----------------------------
                # List of attendees
                # -----------------------------

                "attendees": {
                    "type": "array",

                    "items": {
                        "type": "string",
                        "format": "email"
                    }
                },

                # -----------------------------
                # Optional recurrence
                # -----------------------------

                "recurrence": {
                    "type": "object",

                    "properties": {

                        "frequency": {
                            "enum": [
                                "daily",
                                "weekly",
                                "monthly"
                            ]
                        },

                        "count": {
                            "type": "integer",
                            "minimum": 1
                        }
                    }
                }
            },

            # These fields MUST be provided
            # when Claude calls the tool.

            "required": [
                "title",
                "start",
                "end"
            ]
        }
    }
]


# ============================================================
# STEP 3: Define the ACTUAL Python tool
# ============================================================

# This is different from the tool definition above.
#
# The definition tells Claude what the tool looks like.
#
# This function is what YOUR APPLICATION actually executes.


def create_calendar_event(
    title,
    start,
    end,
    attendees=None,
    recurrence=None
):

    print("\n--- Executing create_calendar_event() ---")

    print("Title:", title)
    print("Start:", start)
    print("End:", end)
    print("Attendees:", attendees)
    print("Recurrence:", recurrence)

    # --------------------------------------------------------
    # REAL APPLICATION:
    #
    # Here you would call Google Calendar / Outlook / etc.
    #
    # For example:
    #
    # calendar_api.create_event(...)
    #
    # --------------------------------------------------------

    # For this tutorial, we simulate the calendar API.

    result = {
        "event_id": "evt_123",
        "status": "created"
    }

    return result


# ============================================================
# STEP 4: Create the user's message
# ============================================================

user_message = (
    "Schedule a 30-minute sync with "
    "alice@example.com and bob@example.com "
    "on Monday, March 30, 2026 at 10am."
)


messages = [
    {
        "role": "user",
        "content": user_message
    }
]


# ============================================================
# STEP 5: Send the user's request + tool definition to Claude
# ============================================================

print("Sending request to Claude...")

response = client.messages.create(

    model="claude-opus-5",

    max_tokens=1024,

    # Give Claude access to the tool
    tools=tools,

    # Claude can decide whether to use the tool.
    # Only one tool call is allowed in this turn.
    tool_choice={
        "type": "auto",
        "disable_parallel_tool_use": True
    },

    # Send conversation
    messages=messages
)


# ============================================================
# STEP 6: Check why Claude stopped
# ============================================================

print("\nClaude stop reason:")
print(response.stop_reason)


# If Claude wants to use the tool, stop_reason will be:
#
# "tool_use"
#
# That means:
#
# "Claude isn't finished. It wants our application
#  to execute a tool."


# ============================================================
# STEP 7: Find Claude's tool_use block
# ============================================================

tool_use = next(
    block
    for block in response.content
    if block.type == "tool_use"
)


# ============================================================
# STEP 8: Look at what Claude generated
# ============================================================

print("\n--- Claude's Tool Request ---")

print("Tool name:")
print(tool_use.name)

print("\nTool ID:")
print(tool_use.id)

print("\nTool input:")
print(tool_use.input)


# Claude might generate something like:
#
# {
#     "title": "30-minute sync",
#     "start": "2026-03-30T10:00:00",
#     "end": "2026-03-30T10:30:00",
#     "attendees": [
#         "alice@example.com",
#         "bob@example.com"
#     ]
# }
#
# IMPORTANT:
#
# Claude generated this input.
#
# We did NOT manually create these values.


# ============================================================
# STEP 9: Extract Claude's arguments
# ============================================================

title = tool_use.input["title"]

start = tool_use.input["start"]

end = tool_use.input["end"]


# attendees is optional, so use .get()

attendees = tool_use.input.get(
    "attendees",
    []
)


# recurrence is also optional

recurrence = tool_use.input.get(
    "recurrence"
)


# ============================================================
# STEP 10: Execute the actual Python tool
# ============================================================

result = create_calendar_event(

    title=title,

    start=start,

    end=end,

    attendees=attendees,

    recurrence=recurrence
)


print("\n--- Tool Result ---")
print(result)


# result might be:
#
# {
#     "event_id": "evt_123",
#     "status": "created"
# }


# ============================================================
# STEP 11: Add Claude's previous response to the conversation
# ============================================================

messages.append(
    {
        "role": "assistant",

        # This is Claude's tool_use response.
        #
        # We need to preserve it so Claude knows
        # what tool it previously requested.

        "content": response.content
    }
)


# ============================================================
# STEP 12: Create the tool_result
# ============================================================

tool_result = {
    "type": "tool_result",

    # This MUST match the ID Claude gave us
    # in its tool_use block.

    "tool_use_id": tool_use.id,

    # Convert Python dictionary into JSON text

    "content": json.dumps(result)
}


# ============================================================
# STEP 13: Add the tool result to the conversation
# ============================================================

messages.append(
    {
        "role": "user",

        "content": [
            tool_result
        ]
    }
)


# ============================================================
# STEP 14: Send the tool result back to Claude
# ============================================================

print("\nSending tool result back to Claude...")

followup = client.messages.create(

    model="claude-opus-5",

    max_tokens=1024,

    tools=tools,

    tool_choice={
        "type": "auto",
        "disable_parallel_tool_use": True
    },

    messages=messages
)


# ============================================================
# STEP 15: Check Claude's new stop reason
# ============================================================

print("\nClaude's second stop reason:")
print(followup.stop_reason)


# This time we expect:
#
# "end_turn"
#
# because Claude now has the tool result
# and can answer the user.


# ============================================================
# STEP 16: Extract Claude's final answer
# ============================================================

final_text = next(
    block.text
    for block in followup.content
    if block.type == "text"
)


# ============================================================
# STEP 17: Print final answer
# ============================================================

print("\n--- Claude's Final Answer ---")

print(final_text)