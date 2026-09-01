"""
Claude Structured Outputs
=========================

Structured outputs make Claude return data that follows a schema.

Two related features:

    1. JSON outputs
       → Controls Claude's FINAL response format.

    2. Strict tool use
       → Guarantees TOOL INPUTS follow the tool schema.

Think:

    JSON output
        ↓
    "What Claude returns"

    Strict tool
        ↓
    "How Claude calls my tool"


Basic flow:

    User
      ↓
    Claude
      ↓
    Structured JSON
      ↓
    Your application


Without structured outputs:

    Claude → free-form text → your parser

With structured outputs:

    Claude → schema-compliant JSON → your application
"""


import json
import anthropic
from pydantic import BaseModel


client = anthropic.Anthropic()


# ============================================================
# 1. JSON OUTPUT — RAW JSON SCHEMA
# ============================================================

"""
Use JSON outputs when you want Claude's response itself to
follow a specific JSON structure.

The current API uses:

    output_config={
        "format": {
            "type": "json_schema",
            "schema": {...}
        }
    }
"""

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": (
                "Extract the contact information: "
                "John Smith, john@example.com, "
                "interested in the Enterprise plan."
            ),
        }
    ],
    output_config={
        "format": {
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "plan": {"type": "string"},
                },
                "required": ["name", "email", "plan"],
                "additionalProperties": False,
            },
        }
    },
)

text = next(
    block.text
    for block in response.content
    if block.type == "text"
)

data = json.loads(text)

print(data)
print(data["name"])
print(data["email"])


# ============================================================
# 2. JSON OUTPUT WITH PYDANTIC — RECOMMENDED
# ============================================================

"""
With Python, `client.messages.parse()` can use a Pydantic model.

Instead of manually writing JSON Schema:

    class ContactInfo(BaseModel):
        ...

The SDK generates/transforms the schema and validates the result.

You get:

    response.parsed_output

instead of manually calling:

    json.loads(...)
"""


class ContactInfo(BaseModel):
    name: str
    email: str
    plan: str


response = client.messages.parse(
    model="claude-opus-5",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": (
                "Extract contact information: "
                "John Smith, john@example.com, "
                "interested in the Pro plan."
            ),
        }
    ],
    output_format=ContactInfo,
)

contact = response.parsed_output

print("\nPydantic result:")
print(contact)
print(contact.name)
print(contact.email)


# ============================================================
# 3. WHY STRUCTURED OUTPUTS?
# ============================================================

"""
Without structured outputs:

    Claude
      ↓
    "John's email is john@example.com..."
      ↓
    Your parser
      ↓
    Possible parsing failure


With structured outputs:

    Claude
      ↓
    {
        "name": "...",
        "email": "...",
        "plan": "..."
    }
      ↓
    Your application


Benefits:

    ✓ Valid JSON
    ✓ Required fields
    ✓ Correct data types
    ✓ Predictable structure
"""


# ============================================================
# 4. STRICT TOOL USE
# ============================================================

"""
JSON outputs control Claude's response.

Strict tool use controls Claude's TOOL INPUT.

Use:

    "strict": True

This guarantees that the tool arguments conform to the
provided schema.
"""

tools = [
    {
        "name": "search_flights",
        "description": "Search for available flights.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "destination": {"type": "string"},
                "date": {"type": "string"},
            },
            "required": ["destination", "date"],
            "additionalProperties": False,
        },
    }
]

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=1024,
    tools=tools,
    messages=[
        {
            "role": "user",
            "content": "Find flights to Paris on May 15, 2026.",
        }
    ],
)

if response.stop_reason == "tool_use":

    tool_use = next(
        block
        for block in response.content
        if block.type == "tool_use"
    )

    print("\nTool:", tool_use.name)
    print("Input:", tool_use.input)


# ============================================================
# 5. JSON OUTPUT + STRICT TOOL USE
# ============================================================

"""
You can use BOTH features in the same request.

                    Claude
                       ↓
            ┌──────────┴──────────┐
            ↓                     ↓
      Strict tool use        JSON output
            ↓                     ↓
     Valid tool inputs      Valid final JSON
            ↓                     ↓
       Tool execution          Answer


This is especially useful for agentic applications.
"""

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=1024,

    # Controls Claude's final response.
    output_config={
        "format": {
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string"},
                    "next_steps": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["summary", "next_steps"],
                "additionalProperties": False,
            },
        }
    },

    # Controls Claude's tool arguments.
    tools=[
        {
            "name": "search_flights",
            "description": "Search available flights.",
            "strict": True,
            "input_schema": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string"},
                    "date": {"type": "string"},
                },
                "required": ["destination", "date"],
                "additionalProperties": False,
            },
        }
    ],

    messages=[
        {
            "role": "user",
            "content": "Plan a trip to Paris on May 15, 2026.",
        }
    ],
)


# ============================================================
# 6. STRUCTURED OUTPUT + STOP REASONS
# ============================================================

"""
Structured output normally guarantees schema compliance.

But two important cases can prevent valid structured JSON:

    refusal
        → Claude refused the request.

    max_tokens
        → Claude ran out of output tokens.

Therefore always check stop_reason when reliability matters.
"""

if response.stop_reason == "refusal":
    print("Claude refused the request.")

elif response.stop_reason == "max_tokens":
    print("Output was truncated. Increase max_tokens.")

else:
    print("Structured response received.")


# ============================================================
# 7. SCHEMA COMPLEXITY
# ============================================================

"""
Structured outputs compile your schema into a grammar.

Very complex schemas can become expensive to compile.

Keep schemas:

    ✓ Simple
    ✓ Flat where possible
    ✓ With limited optional fields
    ✓ With limited union types

Current documented limits include:

    Strict tools per request     → 20
    Optional parameters         → 24
    Union-type parameters       → 16

If the schema is too complex, simplify it or split the work
across multiple requests.
"""


# ============================================================
# 8. IMPORTANT DIFFERENCE
# ============================================================

"""
                 JSON OUTPUT              STRICT TOOL

Purpose          Final response          Tool arguments

Parameter        output_config.format    strict=True

Controls         What Claude returns     How Claude calls tool

Example          {"name": "..."}         {"location": "Paris"}

Use case         Data extraction         Reliable tool calling
"""


# ============================================================
# 9. AGENTIC MENTAL MODEL
# ============================================================

"""
                    User
                      ↓
                    Claude
                      ↓
             ┌────────┴────────┐
             ↓                 ↓
       Tool call            Final answer
             ↓                 ↓
      strict=True       JSON output schema
             ↓                 ↓
       Valid inputs      Valid JSON
             ↓
      Execute tool
             ↓
       tool_result
             ↓
           Claude
             ↓
        Final JSON


So:

    strict=True
        → reliable tool arguments

    output_config.format
        → reliable final response


Together they give you:

    Reliable tool calls
            +
    Reliable structured responses
            ↓
       More reliable agent
"""
