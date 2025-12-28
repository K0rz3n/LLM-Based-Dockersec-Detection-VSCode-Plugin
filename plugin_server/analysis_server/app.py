from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from prompt_builder import build_prompt
from model_interface import generate_stream
import json
import logging
import time

app = FastAPI()

embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = Chroma(persist_directory="db", embedding_function=embedding)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

class RiskItem(BaseModel):
    risk_type: str
    snippet: str
    start: int
    end: int

class FixRequest(BaseModel):
    dockerfile: str
    predicted_risks: list[RiskItem]


def event_stream(prompt):
    buffer = []
    for chunk in generate_stream(prompt, buffer_size=1):
        buffer.append(chunk)
        if sum(len(c) for c in buffer) > 10:  # 达到一定字符数再 flush
            yield json.dumps({"response": "".join(buffer), "done": False}, ensure_ascii=False) + "\n"
            buffer = []
            time.sleep(0.05)
    if buffer:
        yield json.dumps({"response": "".join(buffer), "done": False}, ensure_ascii=False) + "\n"
    yield json.dumps({"response": "", "done": True}) + "\n"


@app.post("/fix")
async def fix_dockerfile(data: FixRequest):

    # raw = await data.json()
    # logger.info(f"Received JSON: {raw}")
    context_lookup = {}
    # 为每个风险类型做语义检索
    for item in data.predicted_risks:
        retriever = vectorstore.as_retriever(search_kwargs={
            "k": 5,
            "filter": {"risk_label": item.risk_type}
        })
        docs = retriever.get_relevant_documents("Please show all details about this risk type.")
        context_lookup[item.risk_type] = [doc.page_content for doc in docs]

    # 构建 prompt
    prompt = build_prompt(data.dockerfile, [item.model_dump() for item in data.predicted_risks], context_lookup)

    logger.info(f"Prompt generated: {prompt}")

    # 流式输出
    return StreamingResponse(event_stream(prompt), media_type="text/plain")
