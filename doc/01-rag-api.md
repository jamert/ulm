# RAG with API-based Retriever

Initially I thought that it will be very easy project and I still think so. But it's hard to avoid embeddings. If I want to add relevant to the question context using API, then I need somehow make a request the API, and for that I need somehow extract API arguments from the query. I can do it without embeddings using LLM, but then I need to make *two* requests and this is a *chain* already. And I don't want that at this stage of the project.

Then I thought that I can use Google Search API (or DuckDuckGo or whatever). But it's not obvious how to get access, maybe only scraping thing is available to outsiders.

In the end I will make use of API where all of the parameters will be available through settings — Weather API. I can put current location in the settings and make some actually useful small app with this.


