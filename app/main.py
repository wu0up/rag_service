from fastapi import FastAPI, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from typing import List
from datetime import datetime
import api.schema as sc
from config import configs as p
from services.embedding import process_upload_files, delete_documents, delete_collection
from services.retriever_docs import search_documents, get_summary_content
from utils.logger import logger
from utils import transform_structure

tags_metadata = []

app = FastAPI(
        title=p.IAPP_NAME,
        summary="Base on LangChain API Documentation(https://python.langchain.com/docs).",
        description=f"""
        IAPP_NAME::: {p.IAPP_NAME}
        IAPP_API_URL:::{p.IAPP_API_URL}
        """,
        version=p.IAPP_VERSION,
        openapi_tags=tags_metadata,
        servers=[{
            "url": p.IAPP_API_URL
        }])


@app.post("/processing_docs")
async def preprocess_doc(
    files: List[UploadFile] = File(...),
    kdb_id: str = "default"
):
    """
   Processes the uploaded documents and returns the results.

   Args:
       files (List[UploadFile]): A list of uploaded files to be processed.
       kdb_id (str, optional): The ID of the knowledge database to use. Defaults to "default".

   Returns:
       result: The result of processing the uploaded documents.
   """
    result = await process_upload_files(
        files=files,
        kdb_id=kdb_id,
    )

    return result


@app.post("/retriever_docs")
async def retriever_docs(request: sc.QueryInfoRequest):
    """ 
        Retrieve documents based on the provided query and database ID. This endpoint accepts a search query and a knowledge database ID, performs a search to find relevant documents, and returns the retrieved documents. 
        
        Args: 
            text (str): The search query for retrieving relevant documents. 
            kdb_id (str): The identifier for the knowledge database to search within. 
        
        Returns: 
            list: A list of documents that match the search criteria. 
    """ 
    try:
        docs, doc_length, doc_tokens  =await search_documents(request.text, request.kdb_id)
        if p.LLAMAINDEX_FLAG:
            return docs
        else:
            response = transform_structure(docs)
            return response
    except Exception as e:
        return []


@app.delete("/delete_docs")
async def delete_docs(request: sc.DocInfoRequest):
    """
    Retrieve documents based on the provided query and database ID.

    This endpoint accepts a search query and a knowledge database ID, 
    performs a search to find relevant documents, and returns 
    the retrieved documents.

    Args:
        text (str): The search query for retrieving relevant documents.
        kdb_id (str): The identifier for the knowledge database to search within.

    Returns:
        list: A list of documents that match the search criteria.
    """
    
    result  = delete_documents(request.id, request.kdb_id)
    return result

@app.delete("/delete_collection")
async def delete_docs(request: sc.CollectionInfoRequest):
    """
    Retrieve documents based on the provided query and database ID.

    This endpoint accepts a search query and a knowledge database ID, 
    performs a search to find relevant documents, and returns 
    the retrieved documents.

    Args:
        text (str): The search query for retrieving relevant documents.
        kdb_id (str): The identifier for the knowledge database to search within.

    Returns:
        list: A list of documents that match the search criteria.
    """
    
    result  = delete_collection(request.kdb_id)
    return result


@app.post("/get_summary")
async def get_summary(request: sc.ContentRequest):
    """
   Get summary of text content.

   Args:
       request (sc.ContentRequest): The request object containing the text content.

   Returns:
       dict: A dictionary with the result of the summary.
   """
    try:
        result  = get_summary_content(request.text)
        return {'result':result}
    except Exception as e:
        return {'result':""}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
