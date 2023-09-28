import re

import openai
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.text import Text
from unstructured.partition.text_type import sentence_count
from unstructured.staging.base import convert_to_dict
from unstructured.chunking.title import chunk_by_title
from unstructured.cleaners.core import clean_ligatures, clean_extra_whitespace


def process_pdf(filename):
    elements = partition_pdf(filename, strategy="hi_res")
    clean_hyphen = lambda s: s.replace("- ", "")
    remove_cid = lambda s: re.sub(r"\(cid:[0-9]+\)", "", s)
    for e in elements:
        e.apply(clean_ligatures)
        e.apply(clean_hyphen)
        e.apply(clean_extra_whitespace)
        e.apply(remove_cid)
    return elements


def needs_merge(e1: Text, e2: Text) -> bool:
    prompt = f"""
    The following two text snippets are extracted from PDF file.
    We need to decide if snippets look like of one paragraph and assuming snippet 2 is continuation of snippet 1
    
    Snippet 1:
    ```
    {e1.text.split(".")[-1]}
    ```
    
    Snippet 2:
    ```
    {e2.text.split(".")[0]}
    ```

    If text snippets should be merged into one paragraph, respond with `yes`, otherwise, respond `no`.
    """
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}]
    )
    response = completion["choices"][0]["message"]["content"]
    return "yes" in response.lower()


if __name__ == "__main__":
    elements = process_pdf("copyrighted/patchwork.pdf")
    for index, e in enumerate(elements):
        # if sentence_count(e.text) > 2 and e.category != "Title":
        print(index, e.text)
        if index > 20:
            break
