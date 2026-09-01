from anthropic import Anthropic


# ========================================================================================================================
# STEP 1: Create Claude client
# ========================================================================================================================

client = Anthropic()


# ========================================================================================================================
# STEP 2: Define the tools Claude is allowed to use
# ============================================================

# below is the input schema for the tool, which will have: name, description, input_schema, input_examples

tools = [

    # -------------------------
    # Tool 1: Weather
    # -------------------------
    {
        "name": "get_weather",

        "description": "Get the current weather in a given location",

        "input_schema": {
            "type": "object",

            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                }
            },

            "required": ["location"],
        },
    },


    # -------------------------
    # Tool 2: Time
    # -------------------------
    {
        "name": "get_time",

        "description": "Get the current time in a given timezone",

        "input_schema": {
            "type": "object",

            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "The timezone, e.g. America/New_York",
                }
            },

            "required": ["timezone"],
        },
    },
]


# ========================================================================================================================
# STEP 3: User asks a question
# ========================================================================================================================

messages = [
    {
        "role": "user",
        "content": "What's the weather in SF and NYC, and what time is it there?",
    }
]


# ========================================================================================================================
# STEP 4: Send the question + tools to Claude
# ========================================================================================================================

print("Requesting tool calls...")

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=1024,
    messages=messages,
    tools=tools,
)


# ========================================================================================================================
# STEP 5: Find ALL tool calls Claude requested
# ============================================================

tool_uses = [
    block
    for block in response.content
    if block.type == "tool_use"
]

if len(tool_uses) > 1:
    print("Parallel tool calls detected!")
else:
    print("No parallel tool calls detected")

print(f"\nClaude made {len(tool_uses)} tool calls.")


# ========================================================================================================================
# STEP 6: See what Claude requested
# ========================================================================================================================

for tool_use in tool_uses:

    print("\nTool name:")
    print(tool_use.name)

    print("Tool ID:")
    print(tool_use.id)

    print("Tool input:")
    print(tool_use.input)


# ========================================================================================================================
# STEP 7: Execute every requested tool
# ========================================================================================================================

tool_results = []


for tool_use in tool_uses:

    # ----------------------------------------------------------------------------------------------------------------
    # Claude requested get_weather
    # ----------------------------------------------------------------------------------------------------------------

    if tool_use.name == "get_weather":

        location = tool_use.input["location"]

        print(f"\nExecuting get_weather({location})")


        # Simulated weather API (we will actual call weather api here by writing weather api function)
        if "San Francisco" in location:
            result = "San Francisco: 68°F, partly cloudy"

        elif "New York" in location:
            result = "New York: 45°F, clear skies"

        else:
            result = f"Weather unavailable for {location}"


    # ----------------------------------------------------------------------------------------------------------------
    # Claude requested get_time
    # --------------------------------------------------------

    elif tool_use.name == "get_time":

        timezone = tool_use.input["timezone"]

        print(f"\nExecuting get_time({timezone})")


        # Simulated time API
        if timezone == "America/Los_Angeles":
            result = "San Francisco local time: 2:30 PM PST"

        elif timezone == "America/New_York":
            result = "New York local time: 5:30 PM EST"

        else:
            result = f"Time unavailable for {timezone}"


    # ----------------------------------------------------------------------------------------------------------------
    # Unknown tool
    # ----------------------------------------------------------------------------------------------------------------

    else:

        result = f"Unknown tool: {tool_use.name}"


    # ----------------------------------------------------------------------------------------------------------------
    # Save the result
    # ----------------------------------------------------------------------------------------------------------------

    tool_results.append(
        {
            "type": "tool_result",
            "tool_use_id": tool_use.id,
            "content": result,
        }
    )


# ========================================================================================================================
# STEP 8: Add Claude's tool request to conversation
# ============================================================

messages.append(
    {
        "role": "assistant",
        "content": response.content,
    }
)


# ========================================================================================================================
# STEP 9: Send ALL tool results in ONE message
# ========================================================================================================================

messages.append(
    {
        "role": "user",
        "content": tool_results,
    }
)


# ========================================================================================================================
# STEP 10: Send everything back to Claude
# ========================================================================================================================

print("\nSending tool results back to Claude...")

final_response = client.messages.create(
    model="claude-opus-5",
    max_tokens=1024,
    messages=messages,
    tools=tools,
)


# ========================================================================================================================
# STEP 11: Extract Claude's final answer
# ========================================================================================================================

final_text = next(
    block.text
    for block in final_response.content
    if block.type == "text"
)


# ========================================================================================================================
# STEP 12: Print final answer
# ========================================================================================================================

print("\nClaude's response:")
print(final_text)

# Important Notes:
# 1. We can call multiple tools in parallel
# 2. We send all tool results in one message
# 3. Claude processes all results at once
# 4. Claude can combine information from multiple tools
# 5. This is much faster than sequential tool calls
#6. Parallel tool use is on by default. To turn it off, set disable_parallel_tool_use: true inside the tool_choice object. 