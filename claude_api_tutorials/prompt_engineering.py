"""
ANTHROPIC PROMPT ENGINEERING
============================

Core techniques covered:

    1. Be clear and direct
    2. Be specific
    3. Structure prompts with XML tags

Mental model:

    Clear instructions
          +
    Specific requirements
          +
    Structured context
          ↓
       Claude
          ↓
    More consistent output
"""

import anthropic


client = anthropic.Anthropic()


# ============================================================
# 1. BE CLEAR AND DIRECT
# ============================================================

"""
Avoid vague instructions.

BAD:

    "Make this better."

Claude has to guess:
    - What does "better" mean?
    - What tone?
    - How long?
    - Who is the audience?

GOOD:

    Explicitly state the action and desired result.
"""

prompt = """
Rewrite the following email to sound more professional.

Keep the original meaning and keep it under 100 words.

Email:
Hey John, just wanted to check if you saw my last email.
Let me know when you get a chance.
"""

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=500,
    messages=[
        {
            "role": "user",
            "content": prompt,
        }
    ],
)

print(response.content[0].text)


# ============================================================
# 2. BE SPECIFIC
# ============================================================

"""
Clear:

    "Analyze these customer reviews."

Specific:

    - Define what to analyze
    - Define how many items
    - Define priorities
    - Define output format
    - Define constraints
"""

prompt = """
Analyze the following customer reviews.

Identify:
1. The 3 most common complaints
2. The customer impact of each complaint
3. One recommended product improvement for each

Rank the complaints from highest to lowest priority.

Return the result as a table:

| Complaint | Impact | Recommendation | Priority |

Customer reviews:
- The app crashes when I upload large files.
- The dashboard is difficult to navigate.
- Reports take too long to generate.
- The app crashes with large PDF files.
"""

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=1000,
    messages=[
        {
            "role": "user",
            "content": prompt,
        }
    ],
)

print(response.content[0].text)


# ============================================================
# 3. STRUCTURE WITH XML TAGS
# ============================================================

"""
XML tags separate different parts of the prompt.

Common pattern:

    <role>
    <context>
    <task>
    <requirements>
    <input>
    <output_format>

This is especially useful when prompts contain large amounts
of context, retrieved documents, or multiple instructions.
"""

prompt = """
<role>
You are an enterprise customer-support analyst.
</role>

<context>
The customer is an enterprise customer.
They are experiencing API timeouts.
</context>

<task>
Analyze the customer's issue and recommend troubleshooting steps.
</task>

<requirements>
- Identify the 3 most likely causes.
- Rank them by likelihood.
- Give one diagnostic step for each.
- Do not invent information.
- Keep the answer under 300 words.
</requirements>

<output_format>
Use this structure:

Cause:
Evidence:
Diagnostic step:
Recommended action:
</output_format>

<customer_message>
Our API requests have been timing out since yesterday.
</customer_message>
"""

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=1000,
    messages=[
        {
            "role": "user",
            "content": prompt,
        }
    ],
)

print(response.content[0].text)


# ============================================================
# 4. XML FOR RAG / RETRIEVED DOCUMENTS
# ============================================================

"""
XML is particularly useful for RAG.

Separate:

    Instructions
        ↓
    Retrieved documents
        ↓
    User question

This helps Claude distinguish instructions from untrusted
or retrieved content.
"""

prompt = """
<instructions>
Answer the question using only the documents provided.

If the answer cannot be found in the documents,
say: "I don't have enough information."
</instructions>

<documents>

<document id="1">
The refund policy allows refunds within 30 days.
</document>

<document id="2">
Enterprise customers can request refunds through
their account manager.
</document>

</documents>

<question>
Can an enterprise customer request a refund after 20 days?
</question>
"""

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=500,
    messages=[
        {
            "role": "user",
            "content": prompt,
        }
    ],
)

print(response.content[0].text)


# ============================================================
# 5. NESTED XML TAGS
# ============================================================

"""
XML tags can be nested to represent structured information.

Useful for:

    - Customer profiles
    - Documents
    - Products
    - Database records
    - RAG context
"""

prompt = """
<customer>
    <name>Alice</name>
    <plan>Enterprise</plan>

    <issue>
        <type>API timeout</type>
        <started>Yesterday</started>
        <severity>High</severity>
    </issue>
</customer>

<task>
Recommend the first three troubleshooting steps.
</task>
"""

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=500,
    messages=[
        {
            "role": "user",
            "content": prompt,
        }
    ],
)

print(response.content[0].text)


# ============================================================
# 6. COMBINE ALL THREE TECHNIQUES
# ============================================================

"""
Production prompts commonly combine:

    CLEAR
      ↓
    Tell Claude exactly what to do

    SPECIFIC
      ↓
    Define constraints and success criteria

    XML
      ↓
    Separate instructions, context, input and output

Example:

    <role>
        Who Claude is
    </role>

    <context>
        Background information
    </context>

    <task>
        Exact task
    </task>

    <requirements>
        Constraints / success criteria
    </requirements>

    <input>
        Actual data
    </input>

    <output_format>
        Expected response structure
    </output_format>
"""

prompt = """
<role>
You are a senior product analyst.
</role>

<context>
We are evaluating an AI customer-support product.
The product currently has a 12% customer churn rate.
</context>

<task>
Analyze the customer feedback and identify the most important
product problems causing dissatisfaction.
</task>

<requirements>
- Identify the 3 most important problems.
- Explain why each matters.
- Recommend one product improvement for each.
- Rank them by expected business impact.
- Do not make claims unsupported by the feedback.
</requirements>

<output_format>
Return a table:

| Problem | Evidence | Business Impact | Recommendation | Priority |
</output_format>

<customer_feedback>
Customers report that:
1. Responses are sometimes inaccurate.
2. The chatbot takes too long to respond.
3. Users cannot easily escalate to a human.
4. The dashboard is confusing.
5. Some answers are incomplete.
</customer_feedback>
"""

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=1000,
    messages=[
        {
            "role": "user",
            "content": prompt,
        }
    ],
)

print(response.content[0].text)


# ============================================================
# 7. REUSABLE PROMPT TEMPLATE
# ============================================================

"""
A useful production pattern:

    <role>
        ...
    </role>

    <context>
        ...
    </context>

    <task>
        ...
    </task>

    <requirements>
        ...
    </requirements>

    <input>
        ...
    </input>

    <output_format>
        ...
    </output_format>

Keep instructions separate from dynamic data.

For example:

    prompt = TEMPLATE.format(
        customer_data=data
    )

This makes prompts easier to maintain and evaluate.
"""

PROMPT_TEMPLATE = """
<role>
You are a helpful data analyst.
</role>

<task>
Analyze the provided sales data.
</task>

<requirements>
- Identify the top 3 products.
- Explain the trend.
- Keep the answer under 150 words.
</requirements>

<sales_data>
{sales_data}
</sales_data>

<output_format>
Use bullet points.
</output_format>
"""

sales_data = """
Product A: $120,000
Product B: $95,000
Product C: $80,000
Product D: $45,000
"""

prompt = PROMPT_TEMPLATE.format(
    sales_data=sales_data
)

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=500,
    messages=[
        {
            "role": "user",
            "content": prompt,
        }
    ],
)

print(response.content[0].text)
