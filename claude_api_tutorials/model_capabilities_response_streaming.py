"""
Claude Streaming
================

Streaming lets Claude send the response incrementally.

Normal request:

    User
      ↓
    Claude
      ↓
    COMPLETE response
      ↓
    Your application


Streaming:

    User
      ↓
    Claude
      ↓
    chunk → chunk → chunk → chunk
      ↓
    Your application displays them immediately


Use streaming when you want:

    - Faster perceived response time
    - Token-by-token text display
    - Streaming tool inputs
    - Streaming thinking
    - Large responses without waiting for the full response


The Python SDK provides:

    client.messages.stream(...)

and:

    stream.text_stream

for simple text streaming.
"""

import anthropic

client = anthropic.Anthropic()


# ============================================================
# 1. NORMAL API CALL VS STREAMING
# ============================================================

"""
Without streaming:

    response = client.messages.create(...)

    print(response)

You wait for the complete response.

With streaming:

    with client.messages.stream(...) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)

Claude's text arrives incrementally.
"""


# ============================================================
# 2. BASIC STREAMING
# ============================================================

with client.messages.stream(
    model="claude-opus-5",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "Explain RAG in simple terms.",
        }
    ],
) as stream:

    for text in stream.text_stream:
        print(text, end="", flush=True)

print()


# ============================================================
# 3. GET THE COMPLETE MESSAGE
# ============================================================

"""
You can still use streaming internally but get the final
Message object instead of processing every event.

Useful for large responses where you don't need live output.
"""

with client.messages.stream(
    model="claude-opus-5",
    max_tokens=4096,
    messages=[
        {
            "role": "user",
            "content": "Explain transformer architecture.",
        }
    ],
) as stream:

    message = stream.get_final_message()

print("\nFinal message:")

for block in message.content:
    if block.type == "text":
        print(block.text)


# ============================================================
# 4. STREAMING EVENTS
# ============================================================

"""
A stream roughly follows:

    message_start
         ↓
    content_block_start
         ↓
    content_block_delta
         ↓
    content_block_delta
         ↓
    content_block_stop
         ↓
    message_delta
         ↓
    message_stop

The most important event for text is:

    content_block_delta

with:

    delta.type == "text_delta"
"""

with client.messages.stream(
    model="claude-opus-5",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "What is an embedding?",
        }
    ],
) as stream:

    for event in stream:

        if event.type == "content_block_delta":

            if event.delta.type == "text_delta":
                print(event.delta.text, end="", flush=True)

print()


# ============================================================
# 5. STREAMING + stop_reason
# ============================================================

"""
The final message_delta contains information such as:

    stop_reason

For example:

    end_turn
    tool_use
    max_tokens

So streaming does NOT remove the stop_reason concept.

Instead:

    Streaming
       ↓
    Receive events
       ↓
    message_delta
       ↓
    stop_reason
"""

with client.messages.stream(
    model="claude-opus-5",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "Explain vector databases.",
        }
    ],
) as stream:

    message = stream.get_final_message()

print("\nStop reason:", message.stop_reason)


# ============================================================
# 6. STREAMING + TOOL USE
# ============================================================

"""
Tool calls can also be streamed.

The tool input arrives as partial JSON.

Example:

    {"location":
    "San
    Francisco,
    CA"}

These pieces are called:

    input_json_delta

The SDK can accumulate these into the final:

    tool_use.input

Do NOT assume every partial JSON chunk is valid JSON.
"""


tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string"
                }
            },
            "required": ["location"],
        },
    }
]

with client.messages.stream(
    model="claude-opus-5",
    max_tokens=1024,
    tools=tools,
    tool_choice={"type": "any"},
    messages=[
        {
            "role": "user",
            "content": "What's the weather in San Francisco?",
        }
    ],
) as stream:

    message = stream.get_final_message()

print("\nTool response:")

for block in message.content:

    if block.type == "tool_use":
        print("Tool:", block.name)
        print("Input:", block.input)

print("Stop reason:", message.stop_reason)


# ============================================================
# 7. STREAMING + THINKING
# ============================================================

"""
When thinking is enabled, streaming can contain:

    thinking_delta
        ↓
    Thinking content

    text_delta
        ↓
    Final answer

The important event types are:

    thinking_delta
    text_delta

Thinking display can be configured according to the model/API
settings.
"""

with client.messages.stream(
    model="claude-opus-5",
    max_tokens=4096,
    thinking={
        "type": "adaptive",
        "display": "summarized",
    },
    messages=[
        {
            "role": "user",
            "content": "What is 1071 divided by 462?",
        }
    ],
) as stream:

    for event in stream:

        if event.type == "content_block_delta":

            if event.delta.type == "thinking_delta":
                print(
                    "[Thinking]",
                    event.delta.thinking,
                    end="",
                )

            elif event.delta.type == "text_delta":
                print(
                    "\n[Answer]",
                    event.delta.text,
                    end="",
                )

print()


# ============================================================
# 8. STREAMING EVENT FLOW
# ============================================================

"""
                 Claude
                    ↓
              message_start
                    ↓
          content_block_start
                    ↓
          ┌─────────────────┐
          │ content deltas  │
          │                 │
          │ text_delta      │
          │ thinking_delta  │
          │ input_json_delta│
          └─────────────────┘
                    ↓
           content_block_stop
                    ↓
             message_delta
                    ↓
              message_stop


Different content produces different deltas:

    Text       → text_delta
    Tool input → input_json_delta
    Thinking   → thinking_delta
"""


# ============================================================
# 9. STREAMING + LARGE RESPONSES
# ============================================================

"""
For very large max_tokens values, streaming can help keep the
HTTP connection alive.

You can stream internally and simply retrieve the final message:

    with client.messages.stream(...) as stream:
        message = stream.get_final_message()

This gives you the same kind of final Message object as
messages.create().
"""

with client.messages.stream(
    model="claude-opus-5",
    max_tokens=8192,
    messages=[
        {
            "role": "user",
            "content": "Write a detailed explanation of RAG.",
        }
    ],
) as stream:

    final_message = stream.get_final_message()

print(final_message)
