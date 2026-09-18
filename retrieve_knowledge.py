import chromadb
from sentence_transformers import SentenceTransformer
import json
import os

model = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.PersistentClient(path="data/vector_db")

collection = client.get_or_create_collection(
    name="biodiversity_knowledge"
)

# Build the knowledge base automatically if it is empty
if collection.count() == 0:
    folder = "data/knowledge_text"

    documents = []
    doc_ids = []
    metadatas = []

    for filename in os.listdir(folder):
        if filename.endswith(".txt"):
            filepath = os.path.join(folder, filename)

            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()

            documents.append(text)
            doc_ids.append(filename)
            metadatas.append({"source_file": filename})

    if documents:
        embeddings = model.encode(documents).tolist()

        collection.add(
            documents=documents,
            embeddings=embeddings,
            ids=doc_ids,
            metadatas=metadatas
        )


def retrieve_relevant_knowledge(user_question, top_k=3):
    """
    Given a question, find the most relevant knowledge text chunks.
    """
    query_embedding = model.encode([user_question]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )

    return results["documents"][0], results["ids"][0]


def retrieve_structured_facts():
    """
    Loads all your fact-card tables.
    """
    facts = {}

    filenames = [
        "climate_data",
        "soil_data",
        "biodiversity_data",
        "land_cover_data",
        "land_cover_esa_data",
        "deforestation_data"
    ]

    for name in filenames:
        try:
            with open(f"data/structured/{name}.json") as f:
                facts[name] = json.load(f)
        except FileNotFoundError:
            facts[name] = []

    return facts


if __name__ == "__main__":
    question = "My soil has low carbon and low rainfall, what should I do?"

    passages, ids = retrieve_relevant_knowledge(question)
    facts = retrieve_structured_facts()

    print(f"=== Question: {question} ===\n")

    print("=== Top matching knowledge passages ===")

    for doc_id, passage in zip(ids, passages):
        print(f"\n[{doc_id}]")
        print(passage[:300], "...")

    print("\n=== Structured facts loaded ===")

    for name, data in facts.items():
        print(f" - {name}: {len(data)} location(s)")