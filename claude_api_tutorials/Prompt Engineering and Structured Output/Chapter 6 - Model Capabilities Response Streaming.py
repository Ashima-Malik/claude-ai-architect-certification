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

    message_start (a new message is begining, carries the message shell with empty content and inital usage)
         ↓
    content_block_start (a new contenct block is opening with its type(text, tool_use, or thikning) and index) - Make a slot at that index for named block type, a toll_use block opens with its name and id but not any input 
         ↓
    content_block_delta (an incremental piece of block: text, json for input call, thinking fragment)- append the fragment at the block at that index, for tool call input json comes partially, you can't parse them until the blcok closes
         ↓
    content_block_delta (same as above)
         ↓
    content_block_stop (the block at this index is complete) -finalize the block, for text block text will keep on streaming but for tool_use block, this is the first time json is complete enough to parse
         ↓
    message_delta (top level changes to the message: the stop_reason and final usage counts) - record the stop_reason. It tells you whether the model finished or stopped for some other reason
         ↓
    message_stop (the stream is complete) - the assembled content now is the finished message just like the non-streamed response

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

"""
What if streaming stops early becuase of drop connection, timeout or client disconnect:

- Track the completion- a turn is usable only when message_stop has arrived
- Do not save the partial assistant run, retry the request
- check the stop_reason from message_delta, a stop_reason of tool_use means your assembled tool calls are reasy to run, any other values means you are not on a tool path


What streaming handles-

- long responses and user face interface where streaming output keeps them hanging than just waiting for the output
- you assemble blocks yourself and it adds cost and complexity, you must not act on partial blocks and you must handle mid stream interruption explicitly
- for short responses and backend jobs where none is waiting, a non-stream call is simpler and removes the partial state risk entirely


QUICK REVISION-

- A stream ending ≠ a complete message.

- Only message_stop confirms the message finished successfully.

- A network interruption can leave a tool_use block with incomplete/truncated JSON.

- Do not append a streamed assistant turn to history just because the read loop ended.

- If the stream ends before message_stop:

    Discard the incomplete turn.

    Do not store the partial tool_use block.

    Retry from the last complete turn.

Otherwise, the next API request may fail validation because it contains the corrupted tool call.

The error can appear on the retry request, making the schema or retry logic look like the problem.
Production pattern:

Stream starts
    ↓
Receive events
    ↓
message_stop?
   ↙      ↘
 Yes       No
  ↓         ↓
Commit    Discard
history   partial turn
  ↓         ↓
Continue  Retry safely


Key takeaway:

Only commit streamed content to conversation history after message_stop.
"""

