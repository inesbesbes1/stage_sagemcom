from sentence_transformers import SentenceTransformer
import numpy as np

model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

print("Loading model...")
model = SentenceTransformer(model_name)

sentences = [
    "The STB does not wake up after standby",
    "The device fails to resume from sleep mode",
    "The Wi-Fi connection is lost after reboot"
]

embeddings = model.encode(
    sentences,
    normalize_embeddings=True
)

similarity = np.dot(embeddings, embeddings.T)

print("\nEmbedding shape:", embeddings.shape)
print("\nSimilarity matrix:")
print(np.round(similarity, 3))

print("\nModel loaded and tested successfully!")