from llama_index.core.node_parser import SentenceSplitter, SemanticSplitterNodeParser, TokenTextSplitter
from utils.interface import doc_convert_llm
from llama_index.core import DocumentSummaryIndex
from llama_index.core import get_response_synthesizer
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
import json
from llama_index.core import StorageContext
from llama_index.core import load_index_from_storage
from llama_index.core import VectorStoreIndex
# retriever跟index的差異??
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from utils import generate_unique_id
from config import configs as p
from llama_index.core.ingestion import IngestionPipeline, IngestionCache
import os

from llama_index.core.postprocessor.llm_rerank import LLMRerank


class llamaParser:
    def __init__(self, kdb_id:str):
        self.collection = kdb_id
        self.llm, _, self.embedding_model = doc_convert_llm(llamaIndex=True)
        # self.db = chromadb.PersistentClient(path="./chromadb")
        self.db = chromadb.HttpClient(host = p.CHROMA_HOST, port = p.CHROMA_PORT)
        self.chunk_size = 1500
        self.chunk_overlap = 200
        

    async def summaryIndex(self, docs, file_name):

        # summaryindex可能不需要這些
        # chroma_client = chromadb.PersistentClient(path="./chroma_db")
        # chroma_collection = chroma_client.create_collection("ai_arxiv_full")
        # vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        # storage_context = StorageContext.from_defaults(vector_store=vector_store)
        # print("collection", self.collection)
        file_id = generate_unique_id(file_name)
        summary_collection_name = f"summary_{self.collection}_{file_id}"
        chroma_collection = self.db.get_or_create_collection(summary_collection_name)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        # 1024處理沒問題
        splitter = SentenceSplitter(chunk_size=1000 , chunk_overlap=100)

        # Initialize the response synthesizer in 'tree_summarize' mode
        response_synthesizer = get_response_synthesizer(
            llm= self.llm,response_mode="tree_summarize", use_async=True
        )

        # Create the document summary index
        doc_summary_index = DocumentSummaryIndex.from_documents(
            docs,
            llm=self.llm,
            transformations=[splitter],
            storage_context  = storage_context,
            response_synthesizer=response_synthesizer,
            embed_model=self.embedding_model,
            show_progress=True,
            use_async=True
        )
        return True
        # doc_summary_index.storage_context.persist(summary_collection_name)

    async def vectorIndex(self, docs):
        # print("vector collection", self.collection)
        try:
            chroma_collection = self.db.get_or_create_collection(self.collection)
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            # splitter = SentenceSplitter(chunk_size=self.chunk_size,chunk_overlap=self.chunk_overlap)
            # splitter = SemanticSplitterNodeParser(
            # buffer_size=1, breakpoint_percentile_threshold=95, embed_model=self.embedding_model
            # )
            # splitter = TokenTextSplitter(chunk_size=300, chunk_overlap=100)
            pipeline = IngestionPipeline(
                transformations=[
                    # 1024處理沒問題
                    SentenceSplitter(chunk_size=self.chunk_size , chunk_overlap=self.chunk_overlap),
                    self.embedding_model,
                ]
            )
            # nodes = splitter.get_nodes_from_documents(docs)
            nodes = pipeline.run(documents=docs)
            # print('finish nodes', nodes[0])
            try:
                vector_index = VectorStoreIndex(nodes,storage_context=storage_context,  show_progress=True)
            except Exception as e:
                print('err in vectorindex', e)
            # print('finish vector_index')
            
            # index = VectorStoreIndex.from_documents(
            #     docs,
            #     transformations=[splitter],
            #     storage_context  = storage_context,
            #     embed_model=self.embedding_model,
            #     )
            # print('finish vectordb')
        except Exception as e:
            print('err in vectorindex', e)
        return True

    async def rerank_nodes(self, nodes, query):
        ranker = LLMRerank(
            choice_batch_size=10, top_n=3, llm=self.llm
        )
        new_nodes = ranker.postprocess_nodes(nodes, query_str=query)

        return new_nodes
    #re_doc_lst.append({
    #       "text": page_content,
    #        "file_name": decoded_file_name,
    #        "id": unique_id
    #    })

    def transform_array(self, nodes):
        result = []
        for item in nodes:
            # 從每個 NodeWithScore 中提取所需的欄位
            text = item.node.text
            file_name = item.node.metadata.get('file_name', '')
            unique_id = item.node.id_
            
            # 建立新的格式並加入到結果列表
            result.append({
                "text": text,
                "file_name": file_name,
                "id": unique_id
            })
        
        return result

    async def query_vector_engine(self, query):
        collection_lst = self.db.list_collections()
        # print("collection_lst in vector", collection_lst)
        chroma_collection = self.db.get_collection(self.collection)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
        retriever = VectorIndexRetriever(
                        index=index,
                        similarity_top_k=10,
                    )
        nodes = retriever.retrieve(query)
        new_node = await self.rerank_nodes(nodes, query)
        for item in new_node:
            print('item:', item)
        node_output = self.transform_array(new_node)

        return node_output

    async def query_summary_engine(self, query):
        response =[]
        collection_lst = self.db.list_collections()
        collection_lst = [col for col in collection_lst if f"summary_{self.collection}_" in col.name]
        for item in collection_lst:
            temp={}
            # print(f'{item.name} storage_context')
            chroma_collection = self.db.get_collection(self.collection)
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
            query_engine_doc_summary_rerank = index.as_query_engine(
                similarity_top_k=5,
                response_mode="tree_summarize", 
                use_async=True,
                llm=self.llm)   
            res = query_engine_doc_summary_rerank.query(query) 


            response.append(res)
       
        summary = response[0].response
        source_docs = response[0].source_nodes

        return summary, source_docs
    
    # delete summary, vectordb_document-->how to delete document
    def delete_document(self, name):
        try:
            collection_lst = self.db.list_collections()
            print('collection_lst', collection_lst)
            file_id = generate_unique_id(name)
            # delete summary collection
            collection_name =  f"summary_{self.collection}_{file_id}"
            if collection_name in collection_lst:
                print('collection_name', collection_name)
                # lst = self.db.list_collections()
                collection = self.db.get_collection(name =collection_name)
                if collection:
                    self.db.delete_collection(collection_name)
            # delete vectordb collection
            if self.collection in collection_lst:
                collection = self.db.get_collection(name =self.collection)
                docs = collection.get()
                docs_metadata = docs.get('metadatas')
                # print('docs_metadata', docs_metadata)
                delete_doc_ids = []
                for d in docs_metadata:
                    f_name = os.path.splitext(d.get('file_name', ''))[0]
                    print('file_name', f_name)
                    if f_name == name:
                        node_info = json.loads(d.get('_node_content'))
                        print('node_info', node_info)
                        delete_doc_ids.append(node_info.get('id_'))
                        print('delete_doc_ids', delete_doc_ids)
                # 確認是否可以比對document_id, 確認是否能不要比對filetype
                if collection:
                    collection.delete(
                                ids=delete_doc_ids,
                            )
        except Exception as e:
            print('delete collection error', e)
        return True
        

    def delete_collection(self):
        try:
            # delete summary 
            collection_lst = self.db.list_collections()
            collection_lst = [col for col in collection_lst if f"summary_{self.collection}_" in col.name]
            for item in collection_lst:
                collection = self.db.get_collection(name =item.name)
                if collection:
                    self.db.delete_collection(item.name)
            # delete vectordb
            collection = self.db.get_collection(name =self.collection)
            if collection:
                self.db.delete_collection(self.collection)

            collection_lst = self.db.list_collections()
            print(f'delete collection:{self.collection}, get collection_lst:{collection_lst}')
            return True
        except Exception as e:
            print('delete collection error', e)
            return True

            