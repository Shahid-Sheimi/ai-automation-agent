from qdrant_client import QdrantClient

client = QdrantClient(
    url="https://3ffbfc73-ed40-4b6a-a7c7-32a0d6d190c5.eu-central-1-0.aws.cloud.qdrant.io",
    api_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6NzNlOGQyYmUtYjllMy00ZWJjLTgzZTAtYzA0ZDg2ZGVhNzJkIn0.V6qdElv5xIu2rvkufI0VeGWZJFFE2Yi5Ka4Fd85qfXM",
)

print(client.get_collections())