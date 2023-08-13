"""This module contains templates for various prompts used in the app."""


# Map Reduce Summarize Prompt
MAPREDUCE_PROMPT_TEMPLATE = """Question: {question}

Context: {context}

Based on the context, answer the question in a concise summary.
CONCISE SUMMARY:"""

# Refine Summarize Prompt
REFINE_PROMPT_TEMPLATE = (
    "Your job is to produce a final summary\n"
    "We have provided an existing summary up to a certain point: {existing_answer}\n"
    "We have the opportunity to refine the existing summary"
    "(only if needed) with some more context below.\n"
    "------------\n"
    "{text}\n"
    "------------\n"
    "Given the new context, refine the original summary\n"
    "If the context isn't useful, return the original summary."
)
QUESTION_PROMPT_TEMPLATE = """Question: {question}

Context: {text}

Based on the context, answer the question in a concise summary. If the context is not helpful, just say so."""