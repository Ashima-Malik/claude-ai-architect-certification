"""
Anthropic Text Editor Tool
==========================

The Text Editor Tool allows Claude to view, create, and modify
text files. It is useful for:

    - Debugging code
    - Refactoring code
    - Creating tests
    - Adding documentation
    - Fixing syntax errors
    - Modifying text files


TOOL DEFINITION
---------------

The Text Editor Tool is an Anthropic-defined, schema-less tool.

For Claude 4 and later:

    type = "text_editor_20250728"
    name = "str_replace_based_edit_tool"

Unlike custom tools, you do NOT define an input_schema.


BASIC FLOW
----------

    User
      ↓
    Claude
      ↓
    Claude decides a file operation is needed
      ↓
    Text Editor Tool
      ↓
    Your application executes the operation
      ↓
    tool_result
      ↓
    Claude
      ↓
    More file operations?
       /          \
     YES           NO
      ↓             ↓
    Tool          Answer


IMPORTANT:
----------

Claude decides WHAT operation to perform.

Your application actually performs the file operation.

Claude does NOT automatically get unrestricted access to your
filesystem.


SUPPORTED COMMANDS
------------------

1. view
   ----

   View a file or directory.

       {
           "command": "view",
           "path": "app.py"
       }

   Claude can also request specific file lines using:

       "view_range": [10, 30]

   Line numbers are 1-indexed.


2. str_replace
   ------------

   Replace specific text in a file.

       {
           "command": "str_replace",
           "path": "app.py",
           "old_str": "old code",
           "new_str": "new code"
       }

   The old_str must match exactly, including whitespace
   and indentation.


3. create
   ------

   Create a new file.

       {
           "command": "create",
           "path": "test.py",
           "file_text": "print('hello')"
       }


4. insert
   ------

   Insert text after a specific line.

       {
           "command": "insert",
           "path": "app.py",
           "insert_line": 10,
           "insert_text": "new code"
       }

   insert_line = 0 means the beginning of the file.


AGENTIC WORKFLOW
----------------

Example:

    User:
    "Fix the syntax error in primes.py"

            ↓

    Claude
            ↓
    view("primes.py")
            ↓
    Your application reads the file
            ↓
    tool_result
            ↓
    Claude analyzes the code
            ↓
    str_replace(...)
            ↓
    Your application modifies the file
            ↓
    tool_result
            ↓
    Claude
            ↓
    Final answer


MANUAL IMPLEMENTATION
---------------------

The basic implementation is:

    response = client.messages.create(...)

    while response.stop_reason == "tool_use":

        for block in response.content:

            if block.type == "tool_use":

                result = handle_editor_tool(block)

                tool_result = {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                }

        Send tool_result back to Claude.

        Claude may request another operation.

        Repeat until:

            stop_reason == "end_turn"


YOUR APPLICATION EXECUTES THE TOOL
-----------------------------------

You need a handler such as:

    def handle_editor_tool(tool_call):

        command = tool_call.input.get("command")

        if command == "view":
            # Read file

        elif command == "str_replace":
            # Modify file

        elif command == "create":
            # Create file

        elif command == "insert":
            # Insert text


SECURITY
--------

Because the tool can modify files, your application should:

    - Validate file paths
    - Prevent directory traversal
    - Check permissions
    - Restrict allowed directories
    - Create backups before edits
    - Validate tool inputs
    - Handle file errors
    - Verify changes


IMPORTANT FOR str_replace
-------------------------

Do not blindly replace text.

Check the number of matches:

    0 matches
        ↓
    Return "No match found"

    1 match
        ↓
    Perform replacement

    >1 matches
        ↓
    Return "Multiple matches found"

This prevents unintended modifications.


MAX_CHARACTERS
--------------

The 20250728 version supports:

    "max_characters": 10000

This limits the amount of file content returned when viewing
large files.


TEXT EDITOR VS CUSTOM TOOL
--------------------------

CUSTOM TOOL:

    @beta_tool
    def get_weather(...):
        ...

    You define:
        - Function
        - Schema
        - Implementation

    Your application executes the function.


TEXT EDITOR TOOL:

    text_editor_20250728

    Anthropic defines:
        - Tool schema
        - Commands
        - Parameters

    Claude decides the operation.

    YOUR APPLICATION executes the operation.


TEXT EDITOR VS WEB SEARCH
-------------------------

WEB SEARCH:

    Claude
      ↓
    Web Search
      ↓
    Anthropic infrastructure
      ↓
    Search results
      ↓
    Claude


TEXT EDITOR:

    Claude
      ↓
    Text Editor request
      ↓
    YOUR APPLICATION
      ↓
    Filesystem
      ↓
    tool_result
      ↓
    Claude


CORE MENTAL MODEL
-----------------

    Claude
      ↓
    DECIDES what to do
      ↓
    Tool request
      ↓
    YOUR APPLICATION
      ↓
    VALIDATES the request
      ↓
    EXECUTES the file operation
      ↓
    Returns tool_result
      ↓
    Claude
      ↓
    Decides whether another operation is needed
      ↓
    Final answer
"""