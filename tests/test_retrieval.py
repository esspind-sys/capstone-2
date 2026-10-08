import chromadb
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
chroma = chromadb.PersistentClient(path="./data/chroma")
collection = chroma.get_collection("enterprise-docs")

def search(query: str, top_k: int = 2):
    embedding = model.encode([query]).tolist()
    results = collection.query(query_embeddings=embedding, n_results=top_k)
    print(f"\nQUERY: {query}")
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        preview = doc[:90].replace("\n", " ")
        print(f"  [{meta['source']}] distance={dist:.3f}  {preview}...")

search("What is our password and MFA policy?")
search("How do we handle customer complaints?")
search("What are the rules for merging code?")