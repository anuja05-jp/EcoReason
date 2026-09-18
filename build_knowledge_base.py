import chromadb
from sentence_transformers import SentenceTransformer
import os

# Step 1: Load a model that turns text into "meaning numbers" (embeddings).
model = SentenceTransformer('all-MiniLM-L6-v2')

# Step 2: Set up the vector database
client = chromadb.PersistentClient(path="data/vector_db")
collection = client.get_or_create_collection(name="biodiversity_knowledge")

# Step 3: Read every .txt file in your knowledge_text folder
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

# Step 4: Turn each document into an embedding
embeddings = model.encode(documents).tolist()

# Step 5: Store everything in the vector database
collection.add(
    documents=documents,
    embeddings=embeddings,
    ids=doc_ids,
    metadatas=metadatas
)

print(f"Done! Indexed {len(documents)} documents into the vector database.")
for doc_id in doc_ids:
    print(" -", doc_id)