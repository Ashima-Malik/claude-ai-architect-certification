"""
Claude Prompt Evaluation
========================

A practical prompt-evaluation pipeline using Anthropic only.

Flow:

    Test dataset
         ↓
    Run Claude
         ↓
    Collect outputs
         ↓
    ┌──────────────┬──────────────┐
    ↓                             ↓
Code-based grading          Model-based grading
    ↓                             ↓
Deterministic checks        Claude as judge
    └──────────────┬──────────────┘
                   ↓
              Evaluation
                   ↓
          Compare prompts/models


This file covers:

    1. Generate a test dataset
    2. Run a prompt against the dataset
    3. Code-based grading
    4. Model-based grading
    5. Aggregate evaluation results
    6. Compare two prompts
"""

import json
import anthropic


client = anthropic.Anthropic()


# ============================================================
# 1. GENERATE A TEST DATASET
# ============================================================

"""
A good evaluation starts with representative test cases.

Instead of manually creating hundreds of examples, Claude can
generate an initial evaluation dataset.

Each test case contains:

    input
    expected_answer
"""

dataset_prompt = """
Generate 10 test cases for evaluating a customer-support AI.

Return ONLY JSON:

{
    "test_cases": [
        {
            "input": "...",
            "expected_answer": "..."
        }
    ]
}

Cover:
- Easy questions
- Difficult questions
- Different phrasings
- Edge cases
- Questions the model should refuse
"""

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=4096,
    messages=[
        {
            "role": "user",
            "content": dataset_prompt,
        }
    ],
)

dataset_text = next(
    block.text
    for block in response.content
    if block.type == "text"
)

dataset = json.loads(dataset_text)

print("Generated test cases:", len(dataset["test_cases"]))


# ============================================================
# 2. RUN THE PROMPT AGAINST THE TEST DATASET
# ============================================================

"""
Now run the system/prompt being evaluated against every test case.

    Test case
        ↓
    Prompt
        ↓
    Claude
        ↓
    Model output

Store the input, expected answer, and actual answer together.
"""

PROMPT = """
You are a helpful customer-support assistant.
Answer the user's question clearly and accurately.
"""


def run_prompt(user_input):
    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=1024,
        system=PROMPT,
        messages=[
            {
                "role": "user",
                "content": user_input,
            }
        ],
    )

    return next(
        block.text
        for block in response.content
        if block.type == "text"
    )


results = []

for test_case in dataset["test_cases"]:

    actual_answer = run_prompt(test_case["input"])

    results.append(
        {
            "input": test_case["input"],
            "expected_answer": test_case["expected_answer"],
            "actual_answer": actual_answer,
        }
    )


# ============================================================
# 3. CODE-BASED GRADING
# ============================================================

"""
Code-based graders use deterministic Python logic.

Use them when correctness can be checked mechanically.

Examples:

    - Exact match
    - Contains required text
    - JSON schema validation
    - Regex
    - Numeric accuracy
    - Length limits
    - Required fields

Flow:

    Model output
        ↓
    Python function
        ↓
    pass / fail
"""


def exact_match_grader(actual, expected):
    """
    Returns 1 if the answers match exactly, otherwise 0.
    """
    return int(actual.strip().lower() == expected.strip().lower())


def contains_grader(actual, required_text):
    """
    Returns 1 if required text appears in the answer.
    """
    return int(required_text.lower() in actual.lower())


for result in results:

    result["exact_match_score"] = exact_match_grader(
        result["actual_answer"],
        result["expected_answer"],
    )


# ============================================================
# 4. MODEL-BASED GRADING
# ============================================================

"""
Some qualities cannot be reliably checked with simple code.

Examples:

    - Helpfulness
    - Relevance
    - Correctness against a reference
    - Reasoning quality
    - Tone
    - Completeness

Use Claude as an evaluator.

Flow:

    Expected answer
          +
    Actual answer
          ↓
        Claude
          ↓
    score + explanation
"""


def model_grader(input_text, expected, actual):

    grading_prompt = f"""
Evaluate the following AI answer.

Question:
{input_text}

Expected answer:
{expected}

Actual answer:
{actual}

Score the answer from 1 to 5:

1 = Completely incorrect
2 = Mostly incorrect
3 = Partially correct
4 = Mostly correct
5 = Fully correct

Return ONLY JSON:

{{
    "score": 1,
    "reason": "short explanation"
}}
"""

    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": grading_prompt,
            }
        ],
    )

    text = next(
        block.text
        for block in response.content
        if block.type == "text"
    )

    return json.loads(text)


for result in results:

    grade = model_grader(
        result["input"],
        result["expected_answer"],
        result["actual_answer"],
    )

    result["model_score"] = grade["score"]
    result["model_reason"] = grade["reason"]


# ============================================================
# 5. STRUCTURED MODEL GRADING
# ============================================================

"""
For production evaluation, structured output is preferable.

Instead of asking Claude for arbitrary text:

    "Is this answer good?"

define the evaluator's output:

    {
        "score": 1-5,
        "reason": "..."
    }

This makes the evaluation result easier to process.
"""

grading_schema = {
    "type": "object",
    "properties": {
        "score": {
            "type": "integer",
            "minimum": 1,
            "maximum": 5,
        },
        "reason": {
            "type": "string",
        },
    },
    "required": ["score", "reason"],
    "additionalProperties": False,
}


def structured_model_grader(input_text, expected, actual):

    response = client.messages.create(
        model="claude-opus-5",
        max_tokens=512,
        output_config={
            "format": {
                "type": "json_schema",
                "schema": grading_schema,
            }
        },
        messages=[
            {
                "role": "user",
                "content": f"""
Evaluate this answer.

Question:
{input_text}

Expected:
{expected}

Actual:
{actual}

Give a score from 1 to 5.
""",
            }
        ],
    )

    text = next(
        block.text
        for block in response.content
        if block.type == "text"
    )

    return json.loads(text)


# ============================================================
# 6. AGGREGATE RESULTS
# ============================================================

"""
Individual scores are useful, but evaluations usually need
aggregate metrics.

Example:

    Test cases:       100
    Passed:            87
    Pass rate:         87%
    Average judge:    4.3 / 5
"""


exact_scores = [
    result["exact_match_score"]
    for result in results
]

model_scores = [
    result["model_score"]
    for result in results
]

exact_match_rate = sum(exact_scores) / len(exact_scores)

average_model_score = sum(model_scores) / len(model_scores)

print("\nEvaluation Results")
print("------------------")
print("Test cases:", len(results))
print("Exact match rate:", exact_match_rate)
print("Average model score:", average_model_score)


# ============================================================
# 7. COMPARE TWO PROMPTS
# ============================================================

"""
Prompt evaluation becomes useful when comparing versions.

    Prompt A
       ↓
    Evaluation
       ↓
    Score A

    Prompt B
       ↓
    Evaluation
       ↓
    Score B

Then compare:

    Accuracy
    Judge score
    Failure rate
    Cost
    Latency
"""


PROMPT_A = """
Answer customer questions clearly.
"""

PROMPT_B = """
You are an expert customer-support assistant.
Give accurate, concise, actionable answers.
If you do not know something, say so.
"""


def evaluate_prompt(prompt, dataset):

    scores = []

    for test_case in dataset["test_cases"]:

        response = client.messages.create(
            model="claude-opus-5",
            max_tokens=1024,
            system=prompt,
            messages=[
                {
                    "role": "user",
                    "content": test_case["input"],
                }
            ],
        )

        actual = next(
            block.text
            for block in response.content
            if block.type == "text"
        )

        grade = model_grader(
            test_case["input"],
            test_case["expected_answer"],
            actual,
        )

        scores.append(grade["score"])

    return sum(scores) / len(scores)


score_a = evaluate_prompt(PROMPT_A, dataset)
score_b = evaluate_prompt(PROMPT_B, dataset)

print("\nPrompt comparison")
print("-----------------")
print("Prompt A:", score_a)
print("Prompt B:", score_b)


# ============================================================
# 8. COMPLETE EVALUATION PIPELINE
# ============================================================

"""
The complete evaluation system is:

    ┌──────────────────────┐
    │ Generate test data   │
    └──────────┬───────────┘
               ↓
    ┌──────────────────────┐
    │ Run prompt/model     │
    └──────────┬───────────┘
               ↓
    ┌──────────────────────┐
    │ Collect outputs      │
    └──────────┬───────────┘
               ↓
        ┌──────┴──────┐
        ↓             ↓
     Code grader   Claude grader
        ↓             ↓
        └──────┬──────┘
               ↓
       Aggregate metrics
               ↓
        Compare versions
"""


# ============================================================
# 9. WHAT TO USE WHEN
# ============================================================

"""
| Evaluation need          | Grader              |
|--------------------------|---------------------|
| Exact answer             | Code                |
| Number correctness       | Code                |
| JSON structure           | Code                |
| Required fields          | Code                |
| Regex requirement        | Code                |
| Helpfulness              | Model               |
| Relevance                | Model               |
| Completeness             | Model               |
| Tone                     | Model               |
| Semantic correctness     | Model + reference   |

Best practice:

    Use CODE grading whenever possible.

    Use MODEL grading for subjective/semantic qualities.

    Use BOTH when evaluating important AI systems.
"""

