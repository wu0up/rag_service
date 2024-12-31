from llama_index.core.node_parser import SentenceSplitter
from utils.interface import doc_convert_llm
from llama_index.core import DocumentSummaryIndex
from llama_index.core import get_response_synthesizer
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore

from llama_index.core import StorageContext
from llama_index.core import load_index_from_storage
from llama_index.core import VectorStoreIndex
# retriever跟index的差異??
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from utils import generate_unique_id

class llamaParser:
    def __init__(self, kdb_id:str):
        self.collection = kdb_id
        self.llm, _, self.embedding_model = doc_convert_llm(llamaIndex=True)
        self.db = chromadb.PersistentClient(path="./chromadb")
        self.chunk_size = 500
        self.chunk_overlap = 50
        

    async def summaryIndex(self, docs, file_name):

        # summaryindex可能不需要這些
        # chroma_client = chromadb.PersistentClient(path="./chroma_db")
        # chroma_collection = chroma_client.create_collection("ai_arxiv_full")
        # vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        # storage_context = StorageContext.from_defaults(vector_store=vector_store)
        print("collection", self.collection)
        file_id = generate_unique_id(file_name)
        summary_collection_name = f"summary_{self.collection}_{file_id}"
        chroma_collection = self.db.get_or_create_collection(summary_collection_name)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        splitter = SentenceSplitter(chunk_size=300, chunk_overlap=50)

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
        print("collection", self.collection)
        try:
            chroma_collection = self.db.get_or_create_collection(self.collection)
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            splitter = SentenceSplitter(chunk_size=self.chunk_size,chunk_overlap=self.chunk_overlap)
            nodes = splitter.get_nodes_from_documents(docs)
            vector_index = VectorStoreIndex(nodes,storage_context=storage_context)
            
            # index = VectorStoreIndex.from_documents(
            #     docs,
            #     transformations=[splitter],
            #     storage_context  = storage_context,
            #     embed_model=self.embedding_model,
            #     )
            print('finish vectordb')
        except Exception as e:
            print('err in vectorindex', e)
        return True

    async def query_vector_engine(self, query):
        print('query', query)
        # vector_index = VectorStoreIndex(nodes,storage_context=storage_context)
        # vector_index.storage_context.vector_store.persist(persist_path="/content/chroma_db")
        
        # 將vector_index 轉換成拿chromadb, collection_id
        collection_lst = self.db.list_collections()
        print("collection_lst in vector", collection_lst)
        chroma_collection = self.db.get_collection(self.collection)
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
        retriever = VectorIndexRetriever(
                        index=index,
                        similarity_top_k=3,
                    )
        # query_engine = index.as_query_engine(llm=self.llm,similarity_top_k =10)
        # response = query_engine.query(query)
        response_synthesizer = get_response_synthesizer()

        # assemble query engine
        query_engine = RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer,
            node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.5)],
        )
        response = query_engine.query(query)
        nodes = retriever.retrieve(query)
        print('response in vectordb',nodes)
        print('response source', response.response)
        # print('response source', response.metadata)
        return ""

    async def query_summary_engine(self):
        # storage_context = StorageContext.from_defaults(persist_dir=kdb_id)
        # doc_summary_index = load_index_from_storage(llm=self.llm,
        #                                             storage_context=storage_context,
        #                                             embed_model = self.embedding_model)
        # query_engine_doc_summary_rerank = doc_summary_index.as_query_engine(
        #     similarity_top_k=5,
        #     # text_qa_template=text_qa_template,
        #     # node_postprocessors=[cohere_rerank],
        #     llm=self.llm)   

        # response = query_engine_doc_summary_rerank.query(query) 
        
        response =[]
        collection_lst = self.db.list_collections()
        print("collection_lst in summary", collection_lst)
        collection_lst = [col for col in collection_lst if f"summary_{self.collection}_" in col.name]
        for item in collection_lst:
            temp={}
            collection = self.db.get_collection(name =item.name)
            col = collection.get(
                    # include=["documents"]
                )
            file_name = col['metadatas'][0]['doc_id']
            summary = col.get("documents")
            temp["file_name"] = file_name
            temp['summary'] = summary 
            response.append(temp)
        print('response in summary', response)
        return response
    
    # delete summary, vectordb_document-->how to delete document
    def delete_document(self, name):
        file_id = generate_unique_id(name)

        collection_name =  f"summary_{self.collection}_{file_id}"
        # lst = self.db.list_collections()
        collection = self.db.get_collection(name =collection_name)
        if collection:
            self.db.delete_collection(collection_name)
        

    def delete_collection(self):
        lst = self.db.list_collections()
        print('lst in delete', lst)

            