
from config import configs as p
import llama_index.llms.openai as llamaOpenai
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.ollama import OllamaEmbedding
from openai import OpenAI
from utils.logger import logger

def doc_convert_llm(llamaIndex=False):
    try:
        if p.OPENAI_API_TYPE == "openai":
            if llamaIndex:
                client = llamaOpenai.OpenAI(model=p.OPENAI_API_DEPLOYMENT, temperature=0.0)
            else:
                client = OpenAI()
            model = p.OPENAI_API_DEPLOYMENT
            embed_model = OpenAIEmbedding(model=p.OPENAI_API_DEPLOYMENT_EMBEDDING)
        else:
            ## 調整ollama
            client = OpenAI(
                base_url=p.OLLAMA_BASE_URL,  # Ollama's local server URL
                api_key='ollama',  # Required, but not used for local models
            )
            model = p.OLLAMA_BASE_Model
            embed_model = OllamaEmbedding(
            model_name=p.OLLAMA_EMBEDDING_MODEL,
            base_url=p.OLLAMA_BASE_URL,
        )
    except Exception as e:
        logger.error(f"llm connect error:{e}")
        client = OpenAI()
        model = p.OPENAI_API_DEPLOYMENT
    
    return client, model, embed_model