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
        e.apply(clean_ligatures, clean_hyphen, clean_extra_whitespace, remove_cid)
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


def is_garbage(e: Text, e2=None) -> bool:
    if e.category in ("NarrativeText", "Title"):
        return False

    prompt = f"""
    The following text snippet is extracted from PDF file.
    
    Snippet:
    ```
    {e.text}
    ```

    If text snippet is artefact text (page number, name of the journal, metadata about file, etc.) then respond `yes`.
    Otherwise, respond `no`.

    Examples of categorization:
    ```
    3
    ``` -> this is page number -> `yes`
    ```
    EPD: Society and Space 0(0)
    ``` -> this looks like journal name -> `yes`
    ```
    Keywords Adaptation, infrastructure, labor, Mexico City, repair, urban modernity
    ``` -> this is keyword section from the article -> `no`
    ```
    De Coss-Corzo
    ``` -> looks like author's name without context -> `yes`
    """
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    response = completion["choices"][0]["message"]["content"]
    return "yes" in response.lower()


if __name__ == "__main__":
    elements = process_pdf("copyrighted/patchwork.pdf")
    for index, e in enumerate(elements):
        print(index, e.category, e.text)
        # for _ in range(5):

        if index > 40:
            break
