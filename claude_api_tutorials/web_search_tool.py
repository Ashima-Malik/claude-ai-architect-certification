"""
Anthropic Web Search Tool
=========================

The Web Search tool gives Claude access to current web content and
allows Claude to answer questions that depend on up-to-date information.

Unlike client-side tools such as a Python function decorated with
@beta_tool, Web Search is an Anthropic-provided SERVER tool.

The basic flow is:

    User
      ↓
    Claude
      ↓
    Claude decides whether web search is needed
      ↓
    Anthropic Web Search Tool
      ↓
    Search the live web
      ↓
    Search results returned to Claude
      ↓
    Claude may perform additional searches if needed
      ↓
    Claude generates final answer
      ↓
    Answer includes citations


WHEN CLAUDE SEARCHES
-------------------

Claude can search when the request depends on:

    - Recent events, news, or announcements
    - Current prices, rates, scores, or statistics
    - Information about organizations, people, or products that may
      have changed
    - An explicit request to search or look something up

Claude may answer directly without searching for:

    - Stable facts
    - Mathematics
    - Established science fundamentals
    - Coding concepts
    - Creative writing
    - Brainstorming
    - Information already provided in the conversation


WEB SEARCH TOOL VERSIONS
------------------------

web_search_20250305
    Basic web search.

web_search_20260209
    Adds dynamic filtering.

    Claude can use code execution to filter search results before
    relevant results are added to its context, reducing unnecessary
    token usage.

web_search_20260318
    Adds response-inclusion control for agentic workflows in addition
    to the newer web-search capabilities.


SERVER TOOL VS CLIENT TOOL
--------------------------

CLIENT TOOL:

    @beta_tool
    def get_weather(...):
        ...

    Claude requests the tool
          ↓
    Your application / SDK executes the Python function
          ↓
    Your application sends the result back to Claude


SERVER TOOL:

    tools=[
        {
            "type": "web_search_20260318",
            "name": "web_search"
        }
    ]

    Claude requests a web search
          ↓
    Anthropic executes the search
          ↓
    Search results are returned to Claude
          ↓
    Claude generates the answer


IMPORTANT:
----------

You do NOT implement the web-search function yourself.

You do NOT need to write:

    def run_tool(...):
        ...

for the Anthropic Web Search tool.

Anthropic executes the server-side search for you.


BASIC USAGE
-----------

Example:

    import anthropic

    client = anthropic.Anthropic()

    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": "What's the latest news about AI?"
            }
        ],
        tools=[
            {
                "type": "web_search_20260318",
                "name": "web_search"
            }
        ],
    )

    print(response)


HOW THE AGENTIC SEARCH LOOP WORKS
---------------------------------

Claude can perform multiple searches during a single request.

Conceptually:

    User
      ↓
    Claude
      ↓
    Search #1
      ↓
    Search results
      ↓
    Claude evaluates results
      ↓
    Search #2
      ↓
    Search results
      ↓
    Claude evaluates results
      ↓
    ...
      ↓
    Final answer with citations


MAX_USES
--------

max_uses limits how many searches Claude can perform during a request.

Example:

    tools=[
        {
            "type": "web_search_20260318",
            "name": "web_search",
            "max_uses": 5
        }
    ]

This means Claude can perform at most 5 web searches for that request.

If Claude attempts more searches than allowed, the API returns a
web-search tool error with the max_uses_exceeded error code.


DOMAIN FILTERING
----------------

You can restrict searches to specific domains:

    allowed_domains = [
        "nih.gov",
        "nature.com",
        "who.int"
    ]

Example:

    tools=[
        {
            "type": "web_search_20260318",
            "name": "web_search",
            "allowed_domains": [
                "nih.gov",
                "nature.com"
            ]
        }
    ]

Or you can block specific domains:

    blocked_domains = [
        "example.com"
    ]

IMPORTANT:

Use allowed_domains OR blocked_domains.

Do not provide both in the same request.


USER LOCATION
-------------

Search results can be localized using approximate user-location
information.

Example:

    "user_location": {
        "type": "approximate",
        "city": "San Francisco",
        "region": "California",
        "country": "US",
        "timezone": "America/Los_Angeles"
    }


DYNAMIC FILTERING
-----------------

With web_search_20260209 and later versions, Claude can use code
execution to filter search results before the results reach the
context window.

Conceptually:

    Web Search
         ↓
    Many search results
         ↓
    Code-based filtering
         ↓
    Relevant results only
         ↓
    Claude


This can reduce context usage because irrelevant search results do
not need to be passed into Claude's context.


WEB SEARCH VS YOUR OWN RAG
--------------------------

YOUR RAG SYSTEM:

    Your documents
         ↓
    Chunking
         ↓
    Embeddings
         ↓
    Vector database
         ↓
    Retriever
         ↓
    Retrieved documents
         ↓
    LLM


WEB SEARCH:

    User question
         ↓
    Claude
         ↓
    Web Search
         ↓
    Current web content
         ↓
    Claude
         ↓
    Cited answer


The Web Search tool is useful when the required information is on
the public, changing web.

Your RAG system is useful when the required information is inside
your own private or controlled knowledge base.


KEY CONCEPT
-----------

The most important distinction is:

    Claude decides WHEN to search.

    Anthropic executes the search.

    Claude receives the search results.

    Claude decides whether additional searches are necessary.

    Claude produces the final answer with citations.


This is different from a client-side @beta_tool:

    Claude
      ↓
    Tool request
      ↓
    YOUR APPLICATION
      ↓
    YOUR PYTHON FUNCTION
      ↓
    Tool result
      ↓
    Claude


With Web Search:

    Claude
      ↓
    Web Search request
      ↓
    ANTHROPIC INFRASTRUCTURE
      ↓
    Live web search
      ↓
    Search results
      ↓
    Claude


EVOLUTION OF TOOL USE
---------------------

RING 1
------
Manual single tool

    Claude
       ↓
    Tool request
       ↓
    You execute tool
       ↓
    Tool result
       ↓
    Claude
       ↓
    Final answer


RING 2
------
Manual agentic loop

    Claude
       ↓
    Tool
       ↓
    Claude
       ↓
    Tool
       ↓
    Claude
       ↓
    ...
       ↓
    Final answer


RING 3
------
Multiple tools / parallel calls

                 Claude
                    ↓
             ┌──────┼──────┐
             ↓      ↓      ↓
           Tool A Tool B Tool C
             ↓      ↓      ↓
             └──────┼──────┘
                    ↓
                  Claude
                    ↓
                 Answer


TOOL RUNNER
-----------
SDK-managed tool execution

    Claude
       ↓
    Tool request
       ↓
    SDK executes registered Python tool
       ↓
    Tool result
       ↓
    Claude
       ↓
    Additional tools if necessary
       ↓
    Final answer


SERVER TOOLS
------------
Anthropic-managed tools such as Web Search

    Claude
       ↓
    Server tool request
       ↓
    Anthropic infrastructure
       ↓
    Web Search
       ↓
    Results + citations
       ↓
    Claude
       ↓
    Final answer


CORE TAKEAWAY
-------------

There are two important categories to remember:

    CLIENT TOOLS
        Your application executes the tool.

        Example:
            @beta_tool
            def get_weather(...):
                ...


    SERVER TOOLS
        Anthropic executes the tool.

        Example:
            {
                "type": "web_search_20260318",
                "name": "web_search"
            }


The Web Search tool is therefore an Anthropic-provided server tool,
not a Python function that you execute yourself.
"""