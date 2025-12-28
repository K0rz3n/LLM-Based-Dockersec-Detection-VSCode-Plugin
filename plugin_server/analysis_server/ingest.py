import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document

def ingest_excel_to_chroma(path="data/risk_list.xlsx"):
    df = pd.read_excel(path)

    documents = []
    for _, row in df.iterrows():
        content = f"The risk id: {row['risk_id']}\n" \
              f"The risk level: {row['level']}\n" \
              f"The risk label: {row['short_code']}\n" \
              f"The risk name: {row['risk_name']}\n" \
              f"The risk description: {row['description']}\n" \
              f"The risk rationale: {row['rationale']}\n" \
              f"The risk code sample: {row['risk_sample']}\n" \
              f"The risk remediation advice: {row['remediation']}\n" \
              f"The secure code sample: {row['correct_sample']}\n" \
              f"The advantages of this remediation: {row['advantages']}\n" \
              
        documents.append(Document(page_content=content, metadata={"risk_label": row["short_code"]}))

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(documents)

    embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = Chroma.from_documents(chunks, embedding=embedding, persist_directory="db/")
    print("Risk knowledge vectorstore built!")

    results = db.similarity_search("Please show all details about this risk type.", k=5, filter={"risk_label": "use-add-instead-of-copy"})
    for i, doc in enumerate(results):
        print(f"\n🔎 Top {i+1}:\n{doc.page_content}\nMetadata: {doc.metadata}")

if __name__ == "__main__":
    ingest_excel_to_chroma()