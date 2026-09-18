import chromadb
from sentence_transformers import SentenceTransformer
import json

model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path="data/vector_db")
collection = client.get_collection(name="biodiversity_knowledge")

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
        "climate_data",  # now includes pollution (avg_pm2_5_ug_m3, avg_pm10_ug_m3, avg_no2_ug_m3) alongside temp/rainfall
        "soil_data", "biodiversity_data",
        "land_cover_data", "land_cover_esa_data",
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