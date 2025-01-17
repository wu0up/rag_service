from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
from utils.logger import logger
from datetime import datetime
from langsmith import traceable
import os, pytz


class Settings(BaseSettings):
    """LangSmith"""
    LANGCHAIN_TRACING_V2: str = Field("true", env="LANGCHAIN_TRACING_V2")
    LANGCHAIN_API_KEY: str = Field(
        "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",
        env="LANGCHAIN_API_KEY")
    LANGCHAIN_PROJECT: str = Field("AKASHA", env="LANGCHAIN_PROJECT")
    """Baseic Setting"""
    IAPP_NAME: str = Field("Akasha_Server", env="IAPP_NAME")
    IAPP_VERSION: str = Field("1.0.0", env="IAPP_VERSION")
    IAPP_API_URL: str = Field("http://localhost:8006", env="IAPP_API_URL")
    LLAMAINDEX_FLAG: bool = Field(False, env="LLAMAINDEX_FLAG")

    """LLM"""
    OPENAI_API_TYPE: Optional[str] = Field("openai",
                                          env="OPENAI_API_TYPE")
    OPENAI_API_KEY: Optional[str] = Field(None,
                                          env="OPENAI_API_KEY")
    OPENAI_API_DEPLOYMENT: Optional[str] = Field("gpt-4o-mini",
                                                 env="OPENAI_API_DEPLOYMENT")
    OPENAI_API_DEPLOYMENT_EMBEDDING: Optional[str] = Field(
        "text-embedding-3-small", env="OPENAI_API_DEPLOYMENT_EMBEDDING")
    
    """AST"""
    WHISPER_TYPE: Optional[str] = Field("local",
                                          env="WHISPER_TYPE")
    WHISPER_URL:str=Field("http://60.251.156.211:15005", env ="WHISPER_URL")

    """CHROMA"""
    CHROMA_HOST: Optional[str] = Field("chroma-chromadb",
                                     env="CHROMA_HOST")
    CHROMA_PORT: Optional[int] = Field(8000,
                                     env="CHROMA_PORT")
    CHROMA_TOKEN: Optional[str] = Field(None,
                                     env="CHROMA_TOKEN")
    
    class Config:
        env_file = ".env"


class Config(Settings):

    def __init__(self):
        super().__init__()
        self.setup_environment()

    def setup_environment(self):
        os.environ["LANGCHAIN_TRACING_V2"] = Settings(
        ).LANGCHAIN_TRACING_V2
        os.environ["LANGCHAIN_API_KEY"] = Settings().LANGCHAIN_API_KEY
        os.environ["LANGCHAIN_PROJECT"] = Settings().LANGCHAIN_PROJECT
        os.environ["OPENAI_API_KEY"] = Settings().OPENAI_API_KEY


@lru_cache()
def get_configs():
    configs = Config()
    config_vars = vars(configs)
    for key, value in config_vars.items():
        if key.isupper() and key not in (
                "ENSAAS_SERVICES", "OPENAI_API_KEY", "CHROMA_TOKEN") and value is not None:
            if 'KEY' not in key:
                logger.debug(f"{key} ok ... : {value}")

    return configs


configs = get_configs()
