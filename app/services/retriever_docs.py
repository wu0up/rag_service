from typing import List, Tuple
from langchain_chroma import Chroma
from langchain_core.documents import Document
from config import configs as p
import akasha
from utils import search_folders_by_keyword
from utils.logger import logger
from services.llamaIndex import llamaParser

sum = akasha.Summary( chunk_size=3000, chunk_overlap=100, model =p.OPENAI_API_DEPLOYMENT)

# output doc summary and metadata
async def search_documents(
    query: str,
    folder_name: str,
    search_type: str = "auto",
    max_input_tokens: int = 1000,
    use_rerank: bool = True,
    language: str = "ch"
) -> Tuple[List[Document], int, int]:
    """
    搜尋文件並返回相關的文檔

    Args:
        query (str): 搜尋查詢
        folder_name (str): 要搜尋的資料夾名稱關鍵字
        search_type (str, optional): 搜尋類型. Defaults to "auto".
        max_input_tokens (int, optional): 最大輸入 token 數. Defaults to 3000.
        use_rerank (bool, optional): 是否使用重排序. Defaults to True.
        language (str, optional): 語言. Defaults to "ch".

    Returns:
        Tuple[List[Document], int, int]: 
            - 搜尋到的文檔列表
            - 文檔長度
            - 文檔 token 數

    Raises:
        Exception: 當搜尋過程中發生錯誤時
    """
    # query 相似語意 + summary(直接查chroma : kdb_id+file_name)
    if p.LLAMAINDEX_FLAG:
        llama = llamaParser(kdb_id=folder_name)
        # summary =await llama.query_summary_engine(query)
        # 查詢vectordb會出現empty response
        similar_docs =await llama.query_vector_engine(query)

        return similar_docs, None, None
    
    else:
        logger.info(f"[search_documents] in search_documents")
        embedding_model = 'openai:'+p.OPENAI_API_DEPLOYMENT_EMBEDDING
        base_path = 'chromadb'
        emb_obj = akasha.handle_embeddings(embedding_model)
        try:
            # 1. 找到匹配的 ChromaDB 路徑
            chromadb_paths = search_folders_by_keyword(folder_name, base_path)
            if not chromadb_paths:
                logger.error(f"[search_documents]找不到與關鍵字: '{folder_name}' 匹配的資料夾")
                raise Exception(f"找不到與關鍵字 '{folder_name}' 匹配的資料夾")
            
            logger.info(f"[search_documents] find all chromadb_paths")
            # 2. 收集所有檢索器列表

            db =None
            for item in chromadb_paths:
                # 構建完整路徑
                dir_path = f"{base_path}/{item}"
                print('dir_path', dir_path)
                # 創建 Chroma 實例
                docsearch = Chroma(
                    persist_directory=dir_path,
                    embedding_function=emb_obj
                )
                
                # 獲取數據庫實例
                if db == None:
                    db = akasha.dbs(docsearch)
                else:
                    db.add_chromadb(docsearch)

            logger.info(f"[search_documents] start to get_retrivers")
                # 獲取檢索器列表
            retriever_list = akasha.search.get_retrivers(
                db=db,
                embeddings=emb_obj,
                use_rerank=False,
                threshold=0.0,
                search_type=search_type,
                log={}
            )
            logger.info(f"[search_documents] end to get_retrivers")
            # print('retriever_list', retriever_list)
            # retriever_lsts.extend(retriever_list)
            # 3. 獲取排序後的文檔
            if not retriever_list:
                logger.error(f"[search_documents]沒有找到有效的檢索器")
                raise Exception("沒有找到有效的檢索器")

            logger.info(f"[search_documents] start to get_docs")
            docs, doc_length, doc_tokens = akasha.search.get_docs(
                db,
                emb_obj,
                retriever_list,
                query,
                use_rerank=use_rerank,
                language=language,
                search_type=search_type,
                verbose=False,
                model=p.OPENAI_API_DEPLOYMENT,
                max_input_tokens=max_input_tokens
            )
            logger.info(f"[search_documents] end to get_docs")
            return docs, doc_length, doc_tokens

        except Exception as e:
            logger.error(f"[search_documents]搜尋文檔時發生錯誤: {str(e)}")
            raise Exception(f"搜尋文檔時發生錯誤: {str(e)}")

# 先不使用akasha的function, 因為速度很慢
# output: string only
def get_summary_content(text:str):
    try:
        print("Entering get_summary")
        print(f"Input text length: {len(text)}")
        
        result = sum.summarize_articles(articles = text)
        return result
    except Exception as e:
        logger.error(f"[get_summary]error: {str(e)}")
        raise Exception(f"[get_summary]error: {str(e)}")