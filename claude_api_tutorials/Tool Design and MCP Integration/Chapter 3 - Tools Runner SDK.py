import json

from anthropic import Anthropic, beta_tool


# ============================================================
# STEP 1: Client
# ============================================================

client = Anthropic()


# ============================================================
# STEP 2: Define document search tool
# ============================================================

# When we have the @beta_tool and tools=[get_weather], the runner has access to the executable Python function.

@beta_tool
def search_documents(query: str) -> str:
    """
    Search internal documents for information.

    Args:
        query: Search query.
    """

    print("\n>>> SEARCH_DOCUMENTS CALLED")

    print("Query:", query)


    # --------------------------------------------------------
    # Simulated RAG retrieval
    # --------------------------------------------------------

    results = [
        {
            "title": "San Francisco Climate Report",
            "text": (
                "San Francisco has a cool-summer Mediterranean "
                "climate influenced by the Pacific Ocean."
            )
        },
        {
            "title": "Bay Area Weather",
            "text": (
                "Temperatures are generally mild throughout "
                "the year."
            )
        }
    ]


    return json.dumps(results)


# ============================================================
# STEP 3: Create runner
# ============================================================

runner = client.beta.messages.tool_runner(

    model="claude-opus-5",

    max_tokens=1024,

    tools=[
        search_documents
    ],

    messages=[
        {
            "role": "user",
            "content": (
                "Search for information about "
                "the climate of San Francisco"
            )
        }
    ]
)


# ============================================================
# STEP 4: Iterate through runner
# ============================================================

for message in runner:

    print("\n========================================")
    print("CLAUDE / RUNNER MESSAGE")
    print("========================================")

    print(message.content)


    # ========================================================
    # STEP 5: Generate tool response
    # ========================================================

    tool_response = runner.generate_tool_call_response()


    # ========================================================
    # STEP 6: Did Claude request a tool?
    # ========================================================

    if tool_response is not None:

        print("\nTool response before modification:")

        print(tool_response)


        # ====================================================
        # STEP 7: Modify tool result
        # ====================================================

        for block in tool_response["content"]:

            if block["type"] == "tool_result":

                block["cache_control"] = {
                    "type": "ephemeral"
                }


        # ====================================================
        # STEP 8: Append modified messages
        # ====================================================

        runner.append_messages(
            message,
            tool_response
        )


        print("\nModified tool response:")

        print(tool_response)


"""
Evolution of Tools
==================

Single tool Single turn
------
Manual single tool
       ↓
You execute the tool


RING 2
------
Manual agentic loop
       ↓
You execute tools repeatedly


RING 3
------
Multiple tools parallel calls
       ↓
You execute potentially multiple tool calls


TOOL RUNNER SDK
-----------
       ↓
SDK executes registered Python tools
       ↓
SDK manages the agent loop
       ↓
You can intercept/customize with
generate_tool_call_response()
       ↓
You can manually modify state with
append_messages()
"""