import json
import re
from textwrap import dedent
from pathlib import Path

import openai
import chromadb
import click
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.text import (
    Text,
    element_from_text,
)
from unstructured.cleaners.core import clean_ligatures, clean_extra_whitespace

import ulm.checkpoint as checkpoint


def root(filename: Path) -> Path:
    rootdir = filename.parent.joinpath(filename.stem)
    rootdir.mkdir(exist_ok=True)
    return rootdir


def confirmed(decision: bool, prompt: str, *items: str) -> bool:
    if not decision:
        return decision

    for item in items:
        click.echo(item)
    return click.confirm(prompt, default=decision)


def pdf_to_elements(filename: Path) -> list[Text]:
    rootdir = root(filename)

    with checkpoint.singular(filename=rootdir.joinpath("elements")) as cp:
        if not (elements := cp.saved()):
            elements = partition_pdf(filename, strategy="hi_res")
            clean_hyphen = lambda s: s.replace("- ", "")
            remove_cid = lambda s: re.sub(r"\(cid:[0-9]+\)", "", s)
            for e in elements:
                e.apply(
                    clean_ligatures, clean_hyphen, clean_extra_whitespace, remove_cid
                )

            elements = cp.save(elements)

    with checkpoint.singular(filename=rootdir.joinpath("filtered")) as cp:
        if not (filtered := cp.saved()):
            filtered = cp.save(
                list(
                    filter(
                        lambda e: not confirmed(
                            is_garbage(e)[0], "Is this snippet an artifact?", e.text
                        ),
                        elements,
                    )
                )
            )

    max_index = len(filtered) - 1

    cp = checkpoint.indexed(
        filename=rootdir.joinpath("merged"),
        iterable=filtered,
        initializer=([], set()),
        once_in=5,
    )
    for index, element, (processed, skip_indices) in cp:
        if index in skip_indices:
            continue

        if (
            element.category == "Title"
            or element.text.endswith(".")
            or index == max_index
        ):
            processed.append(element)
            cp.save(index, (processed, skip_indices))
        else:
            max_delta = min(max_index - index, 3)
            for candidate_index in range(index + 1, index + max_delta):
                if confirmed(
                    needs_merge(element, filtered[candidate_index]),
                    "Does it need merge?",
                    element.text,
                    filtered[candidate_index].text,
                ):
                    sep = "" if element.text.endswith(" ") else " "
                    processed.append(
                        element_from_text(
                            sep.join([element.text, filtered[candidate_index].text])
                        )
                    )
                    if confirmed(
                        True,
                        "Can we drop this snippet?",
                        filtered[candidate_index].text,
                    ):
                        skip_indices.add(candidate_index)

                    break

            cp.save(index, (processed, skip_indices))
    else:
        processed, _ = cp.saved()

    return processed


def needs_merge(e1: Text, e2: Text) -> bool:
    p2 = e2.text.split(".")[0]
    return not e1.text.endswith(".") and len(p2) > 30, ""


def is_garbage(e: Text) -> tuple[bool, str]:
    if e.category == "NarrativeText":
        return False, "NarrativeText"

    prompt = dedent(
        f"""
        The following text snippets are extracted from PDF version of scientific journal article on sociology.
        Extraction software extracts all text, including page number, headers with the name of journal, extra metadata, etc.

        Your task is to categorize text snippet to two categories: 'artifact' or 'meaningful'.
        Think step by step. Then in the end of paragraph write final category.
        If text snippet is artefact text (page number, name of the journal, metadata about file, etc.) then respond `yes`.
        Otherwise, respond `no`. Before final desicion, provide explanation for your choice.

        Examples:
        ```
        3
        ```
        This is just a number. It's very likely this is page number. Page number is not part of article text. Artifact
        

        ```
        EPD: Society and Space 0(0)
        ```
        Very short snippet of text is very likely to be an artefact. But we need to make sure this is not a part of the article.
        'Society and Space' could be a name of sociology journal. Also, snippet ends with numbers in cryptic sequence, maybe its a issue number.
        Overall it seems that this snippet is an artifact text from header, because header frequently has journal name or author name. Artifact

        ```
        Keywords Adaptation, infrastructure, labor, Mexico City, repair, urban modernity
        ```
        This looks like Keyword section, wich is common for scientific articles. Also, no journal editor would would put keywords in the headers. Meaningful

        ```
        De Coss-Corzo
        ```
        This sounds like a last name of spanish or portuguese origin. It is very likely to be author's name.
        Author's name is frequently put into page header, so it very likely an artifact. Artifact

        ```
        {e.text}
        ```
        """
    )
    completion = openai.Completion.create(
        model="davinci-002",
        prompt=prompt,
        max_tokens=400,
        stop=["\n"],
        temperature=0,
    )
    response = completion["choices"][0]["text"]
    return "artifact" in [s.strip(" ").lower() for s in response.split(".")], response


def document_to_jsonl(pdf: str, jsonl: str) -> None:
    elements = pdf_to_elements(filename=Path(pdf))
    with Path(jsonl).open("w") as fd:
        for e in elements:
            fd.write(json.dumps(e.to_dict(), ensure_ascii=False))
            fd.write("\n")


class ChromaFactory:
    collection_name = "default"

    @classmethod
    def from_jsonl(cls, jsonl: Path, destination: Path) -> chromadb.Collection:
        client = chromadb.PersistentClient(path=str(destination))
        client.delete_collection(cls.collection_name)
        collection = client.create_collection(cls.collection_name)
        with jsonl.open("r") as fd:
            for line in fd:
                element: dict = json.loads(line)
                if element["type"] == "Title":
                    continue
                collection.add(
                    documents=element["text"],
                    metadatas={
                        key: element.get("metadata", {}).get(key, -1)
                        for key in ["page"]
                    },
                    ids=f"{element['element_id']}",
                )

        return collection

    @classmethod
    def from_path(cls, path: Path) -> chromadb.Collection:
        return chromadb.PersistentClient(path=str(path)).get_collection(
            cls.collection_name
        )


def rag_ask(storage: chromadb.Collection, question: str) -> str:
    retrieved = storage.query(query_texts=question, n_results=5, include=["documents"])
    prompt = (
        "Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.\n"
        + "\n---\n".join(retrieved["documents"][0])
        + f"\nQuestion: {question}"
    )
    completion = openai.ChatCompletion.create(
        messages=[{"role": "user", "content": prompt}], model="gpt-3.5-turbo"
    )

    return completion["choices"][0]["message"]["content"]


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.argument("pdf", type=click.Path(exists=True, path_type=Path))
@click.argument("jsonl", type=click.Path(writable=True, path_type=Path))
def preprocess(pdf: Path, jsonl: Path) -> None:
    document_to_jsonl(pdf, jsonl)


@cli.command()
@click.argument("jsonl", type=click.Path(exists=True, path_type=Path))
@click.argument(
    "db", type=click.Path(dir_okay=True, file_okay=False, writable=True, path_type=Path)
)
def upload(jsonl: Path, db: Path) -> None:
    collection = ChromaFactory.from_jsonl(jsonl, db)


@cli.command()
@click.argument(
    "db", type=click.Path(exists=True, dir_okay=True, file_okay=False, path_type=Path)
)
@click.argument("question", type=str)
def ask(db: Path, question: str) -> None:
    collection = ChromaFactory.from_path(db)
    click.echo(rag_ask(collection, question))
