from fastapi import UploadFile
from typing import List
from datetime import datetime
import logging
from pydantic import BaseModel
from utils.folder_manage import TempFileManager
import akasha
from config import configs as p
from langchain_chroma import Chroma
# import chromadb
import chromadb
from pathlib import Path
from utils import convert_to_urlencoded
import os
import shutil
from services.processing import ProcessDoc
from services.llamaIndex import llamaParser

TempFolder = TempFileManager()

class ProcessResult(BaseModel):
    status: bool
    message: str
    duration: float
    processed_files: int

async def process_upload_files(
    files: List[UploadFile],
    kdb_id: str,
    chunk_size: int = 500
) -> ProcessResult:
    """
    處理上傳的文件：暫存、存入向量資料庫、清理暫存

    Args:
        files: FastAPI 的 UploadFile 列表
        kdb_id: 知識庫的id
        chunk_size: 分塊大小

    Returns:
        ProcessResult: 包含處理狀態、訊息、處理時間和處理檔案數
    """
    start = datetime.now()
    temp_file_paths = []
    contents=[]
    
    try:
        # 使用 TempFileManager 創建臨時文件
        for file in files:
            file_name = file.filename
            content = await file.read()
            temp_file_path = TempFolder.create_temp_files(file_name, content, kdb_id)
            temp_file_paths.append(temp_file_path)
        # temp_file_path = TempFolder.save_file(file.filename, content, folder_name)
        # temp_file_paths.append(temp_file_path)
        # logging.info(f"Successfully created temp files in {temp_file_paths}")
        print(f"Successfully created temp files in {temp_file_paths}")
        # 轉換檔案(image+text: pdf, docx, ppt; image_only:png,jpg, text only:text, mp3)
        # 階段一 -->把所有資料處理成文字
        if p.LLAMAINDEX_FLAG:
            llama = llamaParser(kdb_id=kdb_id)
            process = ProcessDoc()
            contents = await process.wrapper_docs(temp_file_paths)
            print('content', len(content))
            # summary:split content, file_id+kdb_id
            # 慢
            file_name = os.path.splitext(file_name)[0]
            # result = await llama.summaryIndex(contents, file_name)
            # vector_index
            result = await llama.vectorIndex(contents)

        else:
            # 從這邊開始
            # 2. 存入向量資料庫
            embedding_model = "openai:"+p.OPENAI_API_DEPLOYMENT_EMBEDDING
            db_files = akasha.createDB_file(
                file_path=temp_file_paths,
                embeddings=embedding_model,
                chunk_size=chunk_size,
                ignore_check=True
            )
            # logging.info(f"Successfully created vector database entries")
            print(f"Successfully created vector database entries")

        # 3. 清理臨時文件
        TempFolder.cleanup_temp_files(temp_file_paths)
        # logging.info(f"Successfully cleaned up temp files")
        print(f"Successfully cleaned up temp files")

        end = datetime.now()
        duration = (end - start).total_seconds()

        return ProcessResult(
            status=True,
            message="Successfully processed all files",
            duration=duration,
            processed_files=len(files)
        )

    except Exception as e:
        print('error in process_upload_files', e)
        # 確保即使發生錯誤也清理臨時文件
        if temp_file_paths:
            try:
                TempFolder.cleanup_temp_files(temp_file_paths)
            except Exception as cleanup_error:
                logging.error(f"Error during cleanup: {cleanup_error}")

        error_message = f"Error processing files: {str(e)}"
        logging.error(error_message)
        
        end = datetime.now()
        duration = (end - start).total_seconds()

        return ProcessResult(
            status=False,
            message=error_message,
            duration=duration,
            processed_files=0
        )

# 因為要改用llama index,
# 試試看有沒有辦法把持久化path刪除
# delete document: vectordb: delete_document, summary: summary_delete collection
# delete kdb: vectordb: delete_collection, summary:delete "all" summary_collection
def delete_documents(name, kdb_id):

    # delete_collection=[]
    # base_path = 'chromadb'
    # chromadb_paths = search_folders_by_keyword(kdb_id, base_path)
    # for item in chromadb_paths:
    #     if 'name' in item:
    #         delete_collection.append(item)
    name = os.path.splitext(name)[0]
    if p.LLAMAINDEX_FLAG:
        llama=llamaParser(kdb_id=kdb_id)
        llama.delete_document(name)

    # name = convert_to_urlencoded(name)
    
    # embedding_model = 'openai:'+p.OPENAI_API_DEPLOYMENT_EMBEDDING
    # # emb_obj = akasha.handle_embeddings(embedding_model)
    # base_path = 'chromadb'
    # FOLDER_PATH = Path("./chromadb")
    # temp_test = [file for file in FOLDER_PATH.iterdir() if f"{kdb_id}_{name}" in file.stem]
    # print('temp_test', temp_test)
    # # collection_name = 'a2RidGVzdF9mb3JfZG9jX2Zvcm1hdA_50bae81b985a5629bcfe3f58edf3e725_72651cbaa8a16ac7fee20edcb5aa82ae_openai_text-embedding-3-small_500'
    # temp_test.append("default_AI讀書會-20241115161028_78a733fda58ff0f44d5f7f6bee5fe738_openai_text-embedding-3-small_500")
    # for file in temp_test:
    #     # if os.path.exists(file):
    #     #     shutil.rmtree(file)
    #     print('delete file', file)
    #     chroma_client = chromadb.PersistentClient(path=str(file))
    #     lst = chromadb.PersistentClient(str(file)).list_collections()
    #     print('lst in delete', lst)
    #     collection = chroma_client.get_collection()
    #     docs = collection.get(
    #             ids=[],
    #         )
    #     print('docs in delete', docs)
    #     # for item in lst:
    #     #     print("item", item)
    #     #     chroma_client.delete_collection(item) # Remove any data from the chroma store
    #     # # chroma_client.clear_system_cache()
    #     # # chroma_client.reset()
    #     # del chroma_client  # Remove the reference to the client
    #     # collection_name = str(file).replace("chromadb/", "").replace("chromadb\\", "")


    #     # client = chromadb.PersistentClient(str(file))
    #     # collection = client.delete_collection(name=collection_name)
    #     # lst = chromadb.PersistentClient(str(file)).list_collections()
    #     # print('coll', lst)
    return True

# delete collection 
def delete_collection(kdb_id):
    if p.LLAMAINDEX_FLAG:
        llama = llamaParser(kdb_id=kdb_id)
        llama.delete_collection()
    return True