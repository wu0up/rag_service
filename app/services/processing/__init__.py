
from config import configs as p
from unstructured.partition.auto import partition
import os
import aiohttp
from aiohttp import ClientTimeout
from openai import OpenAI
import json
from datetime import datetime
os.environ["KMP_DUPLICATE_LIB_OK"]="TRUE"
import asyncio
import os
import tempfile
from typing import List
import mimetypes
from markitdown import MarkItDown
from utils.logger import logger
from utils.interface import doc_convert_llm
from llama_index.core.schema import Document
from pathlib import Path



async def doc_to_text_unstructured(pdf_path):
    elements = partition(filename=pdf_path)
    return '\n'.join([str(el) for el in elements])

class ProcessDoc:
    def __init__(self,):
        self.updatetype = mimetypes.add_type('audio/x-m4a', '.m4a')

    async def transcribe_whisper(self, input_file_path : str):
        result=''

        try:

            if p.WHISPER_TYPE=="local":
                timeout = ClientTimeout() 
                url = f'{p.WHISPER_URL}/v1/transcriptions'
                headers = {
                    'accept': 'application/json',
                    'Authorization': 'Bearer dummy_api_key',  # 替換為您的 API 金鑰
                }

                # 設置要上傳的文件和表單數據
            
                data = aiohttp.FormData()
                data.add_field('file', 
                            open(input_file_path, 'rb'),
                            filename=input_file_path,
                            content_type='audio/mpeg')
                data.add_field('response_format', 'text')
                data.add_field('timestamp_granularities', 'segment')

                print('send transcribe whisper request', datetime.now())
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, headers=headers, data=data) as response:
                        # 打印回應
                        print('response in whisper', response.status, datetime.now())
                        result = await response.json()
                print('resutl in response', result)
                if 'text' in result:
                    return result.get('text')

            else:
                client = OpenAI()

                audio_file= open(input_file_path, "rb")
                Transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
                )
                result = Transcription.text
                return result
        except Exception as e:
            print('error',e)
            return result

    async def convert_doc(self, file_path, file_type,image_tag=False):
        content =""
        try:
            if 'pdf' in file_type:
                content =  await doc_to_text_unstructured(file_path)
            elif image_tag:
            # if image_tag:
                client, model, _ = doc_convert_llm()
                md = MarkItDown(llm_client=client, llm_model=model)
                result = md.convert(file_path)
                content = result.text_content
            else:
                md = MarkItDown()
                result = md.convert(file_path)
                content = result.text_content
        except Exception as e:
            logger.error(f'convert_docs error:{e}')
            
        return content
 

    # 目前不支持csv
    async def wrapper_docs(self, file_path_lst):
        docs =[]
        for file in file_path_lst:
            mime_type, _ = mimetypes.guess_type(file)
            file_name = Path(file).stem
            print("mime_type", mime_type)
            if mime_type.startswith("image/"):
                transcription_result = await self.convert_doc(file,mime_type, image_tag=True)
            elif mime_type.startswith("audio/") or mime_type.startswith("video/"):
                transcription_result = await self.transcribe_whisper(file)
            # elif "excel" in mime_type:
            #     transcription_result = await self.convert_csv(file)
            else:
                transcription_result = await self.convert_doc(file, mime_type)
                
            doc = Document(text=transcription_result,
                           metadata={
                            "file_name": file_name,
                        },)
            doc.doc_id = file_name
            docs.append(doc)
        
        return docs

