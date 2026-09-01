"""
Working with the Anthropic Messages API
=======================================

The Messages API is the core API used to communicate with Claude.

The basic pattern is:

    User
      ↓
    Your application
      ↓
    Messages API
      ↓
    Claude
      ↓
    Response
      ↓
    Your application


IMPORTANT: THE MESSAGES API IS STATELESS
----------------------------------------

Claude does NOT automatically remember previous API requests.

If you want Claude to remember a conversation, your application
must send the previous messages again.

Example:

    Turn 1:

        User → Hello
        Claude → Hello!

    Turn 2:

        User → Explain LLMs

    Your application sends:

        [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hello!"},
            {"role": "user", "content": "Explain LLMs"}
        ]

    Claude can then see the entire conversation.


============================================================
1. BASIC REQUEST
============================================================

The simplest request sends a user message to Claude.

    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": "Hello, Claude"
            }
        ]
    )

The response contains:

    - id
    - role
    - content
    - model
    - stop_reason
    - usage

The actual answer is inside the content array.

Typical structure:

    response.content
        ↓
    [
        TextBlock(...)
    ]

You can extract the text with:

    text = next(
        block.text
        for block in response.content
        if block.type == "text"
    )


============================================================
2. MESSAGE ROLES
============================================================

Messages normally contain:

    role = "user"
    role = "assistant"

Example:

    messages = [
        {
            "role": "user",
            "content": "Hello"
        },
        {
            "role": "assistant",
            "content": "Hello! How can I help?"
        },
        {
            "role": "user",
            "content": "Explain RAG"
        }
    ]

Claude sees this as a conversation:

    User
      ↓
    Assistant
      ↓
    User
      ↓
    Claude generates next response


============================================================
3. MULTI-TURN CONVERSATION
============================================================

Because the Messages API is stateless, your application maintains
the conversation history.

Example:

    messages = []

    messages.append(
        {
            "role": "user",
            "content": "What is RAG?"
        }
    )

    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=1024,
        messages=messages
    )

    messages.append(
        {
            "role": "assistant",
            "content": response.content
        }
    )

Then the user asks another question:

    messages.append(
        {
            "role": "user",
            "content": "How does retrieval work?"
        }
    )

The next API request receives the entire history.

The pattern is:

    User
      ↓
    messages
      ↓
    Claude
      ↓
    response
      ↓
    append response to messages
      ↓
    User
      ↓
    append new user message
      ↓
    Claude


============================================================
4. SYSTEM PROMPT
============================================================

System instructions tell Claude how it should behave.

Use the top-level:

    system="..."

Example:

    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=1024,
        system="You are an expert AI engineer.",
        messages=[
            {
                "role": "user",
                "content": "Explain RAG."
            }
        ]
    )

The flow becomes:

    System instruction
          ↓
    User request
          ↓
    Claude
          ↓
    Answer


IMPORTANT:

A system instruction that applies from the beginning should use
the top-level `system` parameter.


============================================================
5. MID-CONVERSATION SYSTEM MESSAGE
============================================================

Current Claude models that support this feature can also accept
system messages partway through a conversation, subject to the
documented placement rules.

Conceptually:

    User
      ↓
    Assistant
      ↓
    User
      ↓
    System instruction
      ↓
    Claude

This is useful when a new instruction becomes relevant later.

For example:

    messages = [
        {
            "role": "user",
            "content": "Help me analyze this dataset."
        },
        {
            "role": "assistant",
            "content": "Sure."
        },
        {
            "role": "user",
            "content": "Here is the data."
        },
        {
            "role": "system",
            "content": "From this point forward, return concise answers."
        }
    ]

The important distinction is:

    Top-level system
        ↓
    Applies from the beginning

    Mid-conversation system
        ↓
    Introduces an instruction later in the conversation


============================================================
6. ASSISTANT MESSAGES
============================================================

Your application can include previous assistant responses.

Example:

    messages = [
        {
            "role": "user",
            "content": "Hello, Claude"
        },
        {
            "role": "assistant",
            "content": "Hello! How can I help?"
        },
        {
            "role": "user",
            "content": "Explain LLMs."
        }
    ]

The assistant message does NOT have to originate from a previous
API call.

You can create synthetic assistant messages when appropriate.

This is useful for:

    - Conversation management
    - Prompt construction
    - Demonstrations
    - Few-shot prompting
    - Controlling conversation state


============================================================
7. STOP REASON
============================================================

Claude responses contain:

    response.stop_reason

A common successful completion is:

    "end_turn"

Example:

    if response.stop_reason == "end_turn":
        print("Claude finished the response.")

Other stop reasons can indicate things such as:

    - max_tokens
    - tool_use
    - refusal

Your application should inspect stop_reason when building
more advanced workflows.

For example:

    if response.stop_reason == "tool_use":
        # Execute requested tools

    elif response.stop_reason == "end_turn":
        # Claude finished

    elif response.stop_reason == "max_tokens":
        # Response reached token limit


============================================================
8. MAX TOKENS
============================================================

`max_tokens` controls the maximum number of output tokens Claude
can generate.

Example:

    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": "Explain neural networks."
            }
        ]
    )

If Claude reaches the output limit, the response can have:

    stop_reason = "max_tokens"

Do not confuse:

    max_tokens

with the total context window.

The context contains the input conversation plus generated output.


============================================================
9. PREFILLING
============================================================

Historically, you could partially prefill Claude's response by
putting an assistant message at the end of the input.

Example pattern:

    messages = [
        {
            "role": "user",
            "content": "Choose the correct answer: A, B, or C."
        },
        {
            "role": "assistant",
            "content": "The answer is ("
        }
    ]

Claude continues from:

    "The answer is ("

This can be used to constrain or shape the beginning of a response.

IMPORTANT:

Prefilling is NOT supported on Claude 4.6 and later models and
Claude Mythos Preview.

For those models, use:

    - Structured Outputs
    - System instructions
    - Prompting

instead of response prefilling.


============================================================
10. VISION / IMAGE INPUT
============================================================

Claude can receive both text and images.

An image can be supplied using:

    - base64
    - URL
    - Files API reference

Supported image types include:

    image/jpeg
    image/png
    image/gif
    image/webp


The structure is:

    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "url",
                        "url": "IMAGE_URL"
                    }
                },
                {
                    "type": "text",
                    "text": "What is in this image?"
                }
            ]
        }
    ]


The important idea is that `content` does not have to be a string.

It can be an array containing multiple content blocks:

    content = [
        image,
        text
    ]


============================================================
11. TEXT + IMAGE TOGETHER
============================================================

A multimodal request can contain:

    Image
      +
    Text question

Example:

    content=[
        {
            "type": "image",
            "source": {
                "type": "url",
                "url": "IMAGE_URL"
            }
        },
        {
            "type": "text",
            "text": "Describe this image."
        }
    ]

The flow is:

    Image
       +
    User question
       ↓
    Claude
       ↓
    Vision + reasoning
       ↓
    Answer


============================================================
12. MESSAGE CONTENT TYPES
============================================================

The `content` field can be:

    Simple text:

        "Explain RAG."

    OR structured content:

        [
            {
                "type": "text",
                "text": "Explain this image."
            },
            {
                "type": "image",
                ...
            }
        ]

This structured content model is also important when working
with tools.

For example, tool results are represented as content blocks.


============================================================
13. BASIC COMPLETE EXAMPLE
============================================================

A minimal working application looks like:

    import anthropic

    client = anthropic.Anthropic()

    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": "What is retrieval augmented generation?"
            }
        ]
    )

    final_text = next(
        block.text
        for block in response.content
        if block.type == "text"
    )

    print(final_text)


The complete flow is:

    Python application
          ↓
    client.messages.create()
          ↓
    Anthropic Messages API
          ↓
    Claude
          ↓
    response
          ↓
    response.content
          ↓
    text


============================================================
14. MULTI-TURN COMPLETE EXAMPLE
============================================================

A simple conversation manager:

    import anthropic

    client = anthropic.Anthropic()

    messages = []

    # Turn 1
    messages.append(
        {
            "role": "user",
            "content": "What is RAG?"
        }
    )

    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=1024,
        messages=messages
    )

    messages.append(
        {
            "role": "assistant",
            "content": response.content
        }
    )

    # Turn 2
    messages.append(
        {
            "role": "user",
            "content": "What are the main components?"
        }
    )

    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=1024,
        messages=messages
    )

    print(response)


The key idea is:

    messages

is your application's conversation memory.

The API itself is stateless.


============================================================
15. HOW THIS CONNECTS TO TOOL USE
============================================================

The Messages API is also the foundation for the tool-calling
examples you have been learning.

Without tools:

    User
      ↓
    Claude
      ↓
    Answer


With a tool:

    User
      ↓
    Claude
      ↓
    tool_use
      ↓
    Your application executes tool
      ↓
    tool_result
      ↓
    Claude
      ↓
    Answer


The tool-use messages are added to the same conversation history.

This is why you previously saw:

    messages.append(
        {
            "role": "assistant",
            "content": response.content
        }
    )

and then:

    messages.append(
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    ...
                }
            ]
        }
    )


============================================================
16. THE BIG PICTURE
============================================================

Messages API
     │
     ├── Basic request
     │
     ├── Multi-turn conversation
     │
     ├── System instructions
     │
     ├── Vision
     │
     ├── Tool use
     │
     ├── Agentic loops
     │
     └── Structured outputs


The Messages API is therefore the foundation underneath many
of the more advanced Claude capabilities you are learning.


============================================================
KEY TAKEAWAYS
============================================================

1. The Messages API is STATELESS.

   Your application maintains conversation history.


2. `messages` contains the conversation.

       user
       assistant
       user
       assistant
       ...


3. `system` provides high-level instructions.

       system
          ↓
       conversation


4. `content` can contain:

       - Text
       - Images
       - Tool blocks
       - Tool results
       - Other supported content blocks


5. `stop_reason` tells your application why Claude stopped.

       end_turn
       tool_use
       max_tokens
       refusal
       ...


6. Vision uses structured content blocks.

       image + text
             ↓
           Claude


7. Tool use is built on the same Messages API.

       Claude
          ↓
       tool_use
          ↓
       tool_result
          ↓
       Claude


8. For multi-turn applications, YOU maintain the history.

       messages
          ↓
       API
          ↓
       Claude
          ↓
       response
          ↓
       messages
          ↓
       API
          ↓
       Claude


MENTAL MODEL
------------

Think of the Messages API as:

    YOUR APPLICATION
          │
          │ messages
          ▼
    ┌─────────────────┐
    │  Messages API    │
    └────────┬────────┘
             │
             ▼
          CLAUDE
             │
             │ response
             ▼
    YOUR APPLICATION
             │
             ├── Save response
             ├── Execute tools
             ├── Add tool results
             ├── Add next user message
             └── Send history again

This stateless message-history model is the foundation for
building conversations, tool-using agents, and more complex
agentic systems with Claude.
"""

import anthropic


# ============================================================
# BASIC EXAMPLE
# ============================================================

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "What is Retrieval-Augmented Generation?",
        }
    ],
)

print("Claude:")
print(
    next(
        block.text
        for block in response.content
        if block.type == "text"
    )
)


# ============================================================
# MULTI-TURN EXAMPLE
# ============================================================

messages = [
    {
        "role": "user",
        "content": "What is RAG?",
    }
]

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=1024,
    messages=messages,
)

# Save Claude's response to conversation history.
messages.append(
    {
        "role": "assistant",
        "content": response.content,
    }
)

# Add the next user message.
messages.append(
    {
        "role": "user",
        "content": "What are the main components of RAG?",
    }
)

# Send the ENTIRE conversation history again.
response = client.messages.create(
    model="claude-opus-5",
    max_tokens=1024,
    messages=messages,
)

print("\nClaude's second response:")
print(
    next(
        block.text
        for block in response.content
        if block.type == "text"
    )
)