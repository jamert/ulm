# RAG with embeddings

## Materials

1. [Eugene Yan. LLM Patterns // Retrieval-Augmented Generation: To add knowledge](https://eugeneyan.com/writing/llm-patterns/#retrieval-augmented-generation-to-add-knowledge)
2. [Vicky Boykis. What are embeddings?](http://vickiboykis.com/what_are_embeddings/index.html)
3. [Anton Troynikov. Embeddings and Retrieval for LLMs: Techniques and Challenges](https://www.youtube.com/watch?v=kZeOPapQ8yM)


## Thoughts before

I already tried to make an app that can respond to questions using chunks from the scientific paper. It didn't go well, because of extra metainformation that slipped in the extracted from pdf data. This time, I'll use more recent and clean pdf. Or maybe I'll just use markdown document.


## Thoughts in progress

Most of my time currently goes into preparing data, I didn't even begin to make Q&A system over the document. PDFs are hard because of many extra publishing text snippets. I would save a lot of time, if I just processed document manually.

It's hard to force GPT-3.5 to summarize at the end of paragraph (to make Chain-of-Thought-like query). I could force it using davinci-002 model with legacy Completion interface. It has a `stop` marker argument, which was helpful.

In the end, I decided to force interface with Human (me) to confirm destructive actions, like drop, merge or skip text snippet. And even after that I edited JSONL file manually.
