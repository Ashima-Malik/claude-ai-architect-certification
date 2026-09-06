"""
Claude Message Batches
======================

Batch processing lets you submit MANY Claude requests at once
for asynchronous processing.

Normal Messages API:

    Request
      ↓
    Claude
      ↓
    Response immediately


Batch API:

    Many requests
         ↓
    Create batch
         ↓
    Processing
         ↓
    Poll status
         ↓
    Results


Use batches when:

    - You have many independent requests
    - You don't need immediate responses
    - You want lower cost / higher throughput
    - You are running evaluations or bulk processing

Key facts:

    Up to 100,000 requests OR 256 MB per batch
    Most batches finish within 1 hour
    Batch expires after 24 hours
    Results available for 29 days
    Batch pricing = 50% of standard API pricing
"""

import time
import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request


client = anthropic.Anthropic()


# ============================================================
# 1. CREATE A BATCH
# ============================================================

"""
Each request needs:

    custom_id
        → Unique ID used to identify the result.

    params
        → Normal Messages API parameters.
"""

batch = client.messages.batches.create(
    requests=[
        Request(
            custom_id="question-1",
            params=MessageCreateParamsNonStreaming(
                model="claude-opus-5",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": "What is RAG?",
                    }
                ],
            ),
        ),
        Request(
            custom_id="question-2",
            params=MessageCreateParamsNonStreaming(
                model="claude-opus-5",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": "What is fine-tuning?",
                    }
                ],
            ),
        ),
    ]
)

print("Batch ID:", batch.id)
print("Status:", batch.processing_status)


# ============================================================
# 2. BATCH LIFECYCLE
# ============================================================

"""
    create()
       ↓
    in_progress
       ↓
    processing
       ↓
    ended
       ↓
    retrieve results
"""

batch_id = batch.id


# ============================================================
# 3. POLL FOR COMPLETION
# ============================================================

"""
The batch is asynchronous.

You don't wait on the original create() call for Claude's
answers. Instead, poll the batch status.
"""

while True:

    batch = client.messages.batches.retrieve(batch_id)

    print("Status:", batch.processing_status)

    if batch.processing_status == "ended":
        break

    time.sleep(10)


# ============================================================
# 4. RETRIEVE RESULTS
# ============================================================

"""
Results can arrive in ANY order.

Therefore:

    DO NOT match results by position.

Always use:

    custom_id

to identify which request produced the result.
"""

for result in client.messages.batches.results(batch_id):

    print("\nRequest:", result.custom_id)
    print("Result type:", result.result.type)

    if result.result.type == "succeeded":

        message = result.result.message

        text = next(
            block.text
            for block in message.content
            if block.type == "text"
        )

        print("Answer:", text)

    elif result.result.type == "errored":
        print("Request failed")

    elif result.result.type == "canceled":
        print("Request was canceled")

    elif result.result.type == "expired":
        print("Request expired")


# ============================================================
# 5. RESULT TYPES
# ============================================================

"""
Each request can finish as:

    succeeded
        → Claude generated a response

    errored
        → Request failed

    canceled
        → Batch was canceled before request was processed

    expired
        → Batch reached the 24-hour limit

Use custom_id to connect each result to the original request.
"""


# ============================================================
# 6. LIST BATCHES
# ============================================================

"""
You can retrieve batches created in your Workspace.
"""

for batch in client.messages.batches.list(limit=20):
    print(batch.id, batch.processing_status)


# ============================================================
# 7. CANCEL A BATCH
# ============================================================

"""
A processing batch can be canceled.

Cancellation is asynchronous:

    processing
        ↓
    cancel()
        ↓
    canceling
        ↓
    ended
"""

# Uncomment to cancel:
#
# client.messages.batches.cancel(batch_id)


# ============================================================
# 8. BATCH + NORMAL MESSAGES API
# ============================================================

"""
Almost anything supported by the Messages API can be batched:

    ✓ Text
    ✓ Vision
    ✓ Tool use
    ✓ Server tools
    ✓ System prompts
    ✓ Multi-turn conversations
    ✓ Extended thinking
    ✓ Most beta features

But some synchronous features don't apply.

NOT supported:

    ✗ stream=True
    ✗ Fast mode / speed
    ✗ Threads
    ✗ cache_hint / context_hint
    ✗ max_tokens=0
"""

# Example: vision, tools, etc. can still be included inside
# MessageCreateParamsNonStreaming.


# ============================================================
# 9. BATCH + SERVER TOOLS
# ============================================================

"""
Server tools such as:

    - Web search
    - Web fetch
    - Code execution
    - MCP connectors
    - Advisor
    - Tool search

can be used inside batches.

The batch worker runs the server-side agentic loop.

If the result has:

    stop_reason == "pause_turn"

the server-side loop paused.

You can continue that conversation with a follow-up request.
"""


# ============================================================
# 10. BATCH + PROMPT CACHING
# ============================================================

"""
Batch processing supports prompt caching.

Useful when many requests share the same large context.

Example:

    Large shared document
            ↓
    ┌───────┼───────┐
    ↓       ↓       ↓
 Request  Request  Request
    ↓       ↓       ↓
 Question Question Question

Use identical cache_control blocks to improve cache-hit
likelihood.

Batch discount + prompt caching can provide additional savings.
"""


# ============================================================
# 11. BATCH vs NORMAL API
# ============================================================

"""
                    Messages API       Batch API

Execution           Synchronous         Asynchronous

Response            Immediate           Later

Use case            Interactive         Bulk processing

Streaming           ✓                   ✗

Large volume        Less suitable       ✓

Cost                Standard            50% of standard

Typical use         Chat                Evaluation / analysis


NORMAL:

    User
      ↓
    Claude
      ↓
    Answer


BATCH:

    Request 1 ─┐
    Request 2 ─┤
    Request 3 ─┤
    Request 4 ─┘
          ↓
       Batch
          ↓
      Processing
          ↓
       Results
"""


# ============================================================
# 12. PRACTICAL USE CASE
# ============================================================

"""
Example: evaluate 10,000 RAG answers.

Without batching:

    for question in questions:
        call Claude
        wait
        save result

With batching:

    10,000 requests
          ↓
        Batch
          ↓
    asynchronous processing
          ↓
    10,000 results

This is ideal when you don't need each answer immediately.
"""


# ============================================================
# KEY TAKEAWAY
# ============================================================

"""
Messages API:

    One request
       ↓
    Immediate response


Batch API:

    Many requests
       ↓
    Submit once
       ↓
    Process asynchronously
       ↓
    Poll
       ↓
    Retrieve results


Remember:

    custom_id
        → identifies each request

    processing_status
        → tells you batch status

    results()
        → retrieves individual results

    succeeded / errored / canceled / expired
        → individual request outcomes

    100,000 requests OR 256 MB
        → batch limit

    24 hours
        → processing expiration

    50% pricing
        → batch cost advantage
"""