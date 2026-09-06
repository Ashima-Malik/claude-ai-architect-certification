"""
Claude Effort Parameter
=======================

`effort` controls how much work Claude puts into a response.

It is a behavioral control, NOT a strict token budget.

    low     → faster / cheaper
    medium  → balanced
    high    → default / high quality
    xhigh   → extended reasoning for demanding work
    max     → highest capability, no token-spending constraint

Use:

    output_config={"effort": "medium"}

The setting affects the whole response, including:
    - Text generation
    - Thinking (when active)
    - Tool calls
    - Number/complexity of tool operations
"""


import anthropic

client = anthropic.Anthropic()


# ============================================================
# 1. BASIC USAGE
# ============================================================

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=4096,
    output_config={"effort": "medium"},
    messages=[
        {
            "role": "user",
            "content": "Explain how RAG works.",
        }
    ],
)

print(response.content[0].text)


# ============================================================
# 2. DIFFERENT EFFORT LEVELS
# ============================================================

"""
Choose effort based on the task:

    low
      ↓
    Simple / high-volume / latency-sensitive

    medium
      ↓
    Balanced cost + quality

    high
      ↓
    Complex reasoning / coding / agents

    xhigh
      ↓
    Long-horizon coding / agentic work

    max
      ↓
    Highest possible capability
"""

for effort in ["low", "medium", "high"]:
    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=4096,
        output_config={"effort": effort},
        messages=[
            {
                "role": "user",
                "content": "What is the difference between RAG and fine-tuning?",
            }
        ],
    )

    print(f"\n--- {effort} ---")
    print(response.content[0].text)


# ============================================================
# 3. EFFORT IS NOT max_tokens
# ============================================================

"""
These control different things:

    effort
       → How much work Claude puts into the task

    max_tokens
       → Hard limit on generated output tokens

Think:

    effort = "How hard should Claude work?"

    max_tokens = "How much output space is available?"
"""

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=4096,
    output_config={"effort": "high"},
    messages=[
        {
            "role": "user",
            "content": "Design a production RAG architecture.",
        }
    ],
)


# ============================================================
# 4. EFFORT + TOOLS
# ============================================================

"""
Effort also affects tool use.

Lower effort tends to:
    - Make fewer tool calls
    - Combine operations
    - Act more directly

Higher effort may:
    - Make more tool calls
    - Explore more
    - Provide more detailed explanations

Therefore:

    low effort
        ↓
    fewer / simpler tool operations

    high effort
        ↓
    potentially more extensive agentic work
"""

tools = [
    {
        "name": "search_documents",
        "description": "Search the document database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
            },
            "required": ["query"],
        },
    }
]

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=4096,
    output_config={"effort": "high"},
    tools=tools,
    messages=[
        {
            "role": "user",
            "content": "Find information about our customer retention strategy.",
        }
    ],
)

print("Stop reason:", response.stop_reason)


# ============================================================
# 5. EFFORT + THINKING
# ============================================================

"""
`thinking` and `effort` are different controls.

    thinking
        → Whether/how Claude uses thinking

    effort
        → How much work Claude puts into the overall response

Effort can work with or without thinking.

Do NOT confuse:

    effort="xhigh"

with:

    thinking={"type": "adaptive"}

They control different aspects of the model.
"""


# ============================================================
# 6. CHANGE EFFORT BETWEEN REQUESTS
# ============================================================

"""
`output_config.effort` is request-level.

You can use different effort levels for different requests.

    Easy task
        ↓
    effort="low"

    Complex task
        ↓
    effort="high"

However, if you rely on prompt caching, keep effort constant
within the cached conversation because changing it can invalidate
cached prefixes.
"""

# First request
response = client.messages.create(
    model="claude-opus-5",
    max_tokens=2048,
    output_config={"effort": "low"},
    messages=[
        {
            "role": "user",
            "content": "What is an embedding?",
        }
    ],
)

# Later request can use a different effort level.
response = client.messages.create(
    model="claude-opus-5",
    max_tokens=8192,
    output_config={"effort": "high"},
    messages=[
        {
            "role": "user",
            "content": "Design an enterprise vector search architecture.",
        }
    ],
)


# ============================================================
# 7. PRACTICAL SELECTION
# ============================================================

"""
Task                         Recommended starting point

Simple classification        low
Quick lookup                 low
High-volume application      low / medium
Normal application           medium
Complex reasoning            high
Difficult coding             high
Agentic workflows            high / xhigh
Long-running agent           xhigh
Frontier / hardest problems  max


Do not assume higher is always better.

Test your application with different effort levels and measure:

    - Quality
    - Latency
    - Cost
    - Tool-call count
"""
