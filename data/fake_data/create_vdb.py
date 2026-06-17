import uuid
import os
from dotenv import load_dotenv

from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from openai import OpenAI

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ----------------------------
# Qdrant client
# ----------------------------
qdrant_client = QdrantClient(url="http://localhost:6333")

# ----------------------------
# Text splitter
# ----------------------------
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    separators=["\n\n", "\n", " ", ""],
    length_function=len,
)

# ----------------------------
# Embedding function (OpenAI)
# ----------------------------
def get_embedding(text: str):
    response = client.embeddings.create(
        model="text-embedding-3-large",
        input=text
    )
    return response.data[0].embedding


# ----------------------------
# Config
# ----------------------------
VECTOR_SIZE = 3072


# ----------------------------
# Create collection safely
# ----------------------------
def ensure_collection(name: str):
    if not qdrant_client.collection_exists(name):
        qdrant_client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            )
        )


# ----------------------------
# Ingestion function
# ----------------------------
def ingest(collection_name: str, content: str):
    ensure_collection(collection_name)

    chunks = text_splitter.split_text(content)

    points = []
    for chunk in chunks:
        vector = get_embedding(chunk)
        doc_id = str(uuid.uuid4())

        points.append(
            PointStruct(
                id=doc_id,
                vector=vector,
                payload={"text": chunk}
            )
        )

    qdrant_client.upsert(
        collection_name=collection_name,
        points=points
    )


# ----------------------------
# Load files
# ----------------------------
with open("data/lost_package_policy.md", "r", encoding="utf-8") as f:
    lost_content = f.read()

with open("data/shipping_information.md", "r", encoding="utf-8") as f:
    shipping_content = f.read()


# ----------------------------
# Run ingestion
# ----------------------------
ingest("lost_package_policy", lost_content)
ingest("shipping_information", shipping_content)
print("Data ingestion completed successfully!")