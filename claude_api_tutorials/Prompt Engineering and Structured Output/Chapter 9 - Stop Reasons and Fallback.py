"""
Handling stop_reason in Claude

stop_reason tells your application why Claude stopped.

Common values:

    end_turn
        → Claude finished normally.

    tool_use
        → Claude wants your application to execute a tool.

    max_tokens
        → Claude reached the output token limit.

    stop_sequence
        → Claude reached a configured stop sequence.

    pause_turn
        → A server-tool interaction was paused and can be continued.

    refusal
        → Claude refused to generate the requested content.

    model_context_window_exceeded
        → The request exceeded the model's context window.
"""

import anthropic

client = anthropic.Anthropic()


# ============================================================
# 1. NORMAL RESPONSE → end_turn
# ============================================================

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "What is RAG?",
        }
    ],
)

print("Stop reason:", response.stop_reason)

if response.stop_reason == "end_turn":
    text = next(
        block.text
        for block in response.content
        if block.type == "text"
    )
    print(text)


# ============================================================
# 2. max_tokens
# ============================================================

# Claude stops because it reaches the output limit.

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=10,
    messages=[
        {
            "role": "user",
            "content": "Write a very detailed explanation of RAG.",
        }
    ],
)

print("\nStop reason:", response.stop_reason)

if response.stop_reason == "max_tokens":
    print("Response was truncated. Increase max_tokens or continue.")


# ============================================================
# 3. stop_sequence
# ============================================================

# Claude stops when it generates one of the configured sequences.

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=1024,
    stop_sequences=["END"],
    messages=[
        {
            "role": "user",
            "content": "Write a short explanation of RAG and end with END.",
        }
    ],
)

print("\nStop reason:", response.stop_reason)

if response.stop_reason == "stop_sequence":
    print("Claude stopped at:", response.stop_sequence)


# ============================================================
# 4. tool_use
# ============================================================

tools = [
    {
        "name": "get_weather",
        "description": "Get the weather for a location.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"],
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
            "content": "What's the weather in San Francisco?",
        }
    ],
)

print("\nStop reason:", response.stop_reason)

if response.stop_reason == "tool_use":
    tool_use = next(
        block
        for block in response.content
        if block.type == "tool_use"
    )

    print("Claude wants to call:", tool_use.name)
    print("Arguments:", tool_use.input)


# ============================================================
# 5. The agentic loop
# ============================================================

"""
For client-side tools, tool_use is the signal that tells your
application:

    "Execute the requested tool and send the result back."

The loop continues until Claude returns something other than
tool_use, usually end_turn.
"""

messages = [
    {
        "role": "user",
        "content": "What's the weather in San Francisco?",
    }
]

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=1024,
    tools=tools,
    messages=messages,
)

while response.stop_reason == "tool_use":

    tool_use = next(
        block
        for block in response.content
        if block.type == "tool_use"
    )

    # YOUR APPLICATION executes the tool.
    if tool_use.name == "get_weather":
        result = "68°F, partly cloudy"

    # Add Claude's tool request to the conversation.
    messages.append(
        {
            "role": "assistant",
            "content": response.content,
        }
    )

    # Send the tool result back to Claude.
    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": result,
                }
            ],
        }
    )

    # Ask Claude what to do next.
    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=1024,
        tools=tools,
        messages=messages,
    )

# Eventually:
#
# tool_use
#     ↓
# execute tool
#     ↓
# tool_result
#     ↓
# Claude
#     ↓
# end_turn
#
# The loop stops here.


# ============================================================
# 6. Generic stop_reason handler
# ============================================================

def handle_response(response):
    """
    Use stop_reason as the control signal for your application.
    """

    if response.stop_reason == "tool_use":
        return "Execute the requested tool"

    if response.stop_reason == "max_tokens":
        return "Response was truncated"

    if response.stop_reason == "stop_sequence":
        return "Custom stop sequence reached"

    if response.stop_reason == "pause_turn":
        return "Continue the server-tool interaction"

    if response.stop_reason == "refusal":
        return "Claude refused the request"

    if response.stop_reason == "model_context_window_exceeded":
        return "Context window was exceeded"

    if response.stop_reason == "end_turn":
        return "Claude finished normally"

    return f"Unhandled stop reason: {response.stop_reason}"
