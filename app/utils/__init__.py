import os
import uuid
import base64
import urllib.parse
import hashlib

def search_folders_by_keyword(keyword: str, path: str) -> list[str]:
    """
    搜尋指定路徑下包含關鍵字的資料夾名稱
    
    Parameters:
        keyword (str): 要搜尋的關鍵字
        path (str): 要搜尋的路徑
        
    Returns:
        list[str]: 包含關鍵字的資料夾名稱列表
    
    Raises:
        FileNotFoundError: 當提供的路徑不存在時
        NotADirectoryError: 當提供的路徑不是資料夾時
    """
    
    # 檢查路徑是否存在
    if not os.path.exists(path):
        raise FileNotFoundError(f"路徑不存在: {path}")
    
    # 檢查是否為資料夾
    if not os.path.isdir(path):
        raise NotADirectoryError(f"指定路徑不是資料夾: {path}")
        
    # 儲存符合條件的資料夾名稱
    matching_folders = []
    
    # 使用os.listdir()列出路徑下所有項目
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        # 檢查是否為資料夾且名稱包含關鍵字
        if os.path.isdir(item_path) and keyword.lower() in item.lower():
            matching_folders.append(item)
            
    return matching_folders

def create_uuid(file_name: str):
    uuid_obj = uuid.uuid5(uuid.NAMESPACE_URL, file_name)
    return uuid_obj.hex

def transform_structure(doc_lst):
    # Extract the necessary fields from the input
    re_doc_lst = []
    for item in doc_lst:
        try:
            # Accessing page_content and metadata
            page_content = item.page_content if hasattr(item, 'page_content') else ""
            metadata = item.metadata if hasattr(item, 'metadata') else {}
            file_name = metadata.get("source", "")

            # Decode file_name to support URL encoded strings
            decoded_file_name = urllib.parse.unquote(file_name)
            # Normalizing file path and extracting relevant details
            normalized_path = os.path.normpath(decoded_file_name)
            parts = normalized_path.split(os.sep)
            kdb_id = parts[-2] if len(parts) > 1 else ""
            filename = parts[-1] if parts else ""
            
            # Generating unique ID using a hash of the content
            raw_id = kdb_id + '/' + filename
            unique_id = create_uuid(raw_id)
            
            # Construct the transformed structure
            re_doc_lst.append({
                "text": page_content,
                "file_name": decoded_file_name,
                "id": unique_id
            })
        except Exception as e:
            print('Error processing document:', e)
            re_doc_lst.append({
                "text": "",
                "file_name": "",
                "id": ""
            })
    
    return re_doc_lst


def convert_to_urlencoded(name: str) -> str:
    # 取出名稱部分 (假設格式固定，取第一段以"_"分割的內容)
    base_name = name.split('.')[0]
    print("base_name", base_name)
    # 將名稱進行 URL 編碼
    url_encoded_name = urllib.parse.quote(base_name)
    print("url_encoded_name", url_encoded_name)
    return url_encoded_name


def generate_unique_id(input_str: str) -> int:
    # Hash the input string using SHA-256
    hash_object = hashlib.sha256(input_str.encode())
    # Convert the first 8 characters of the hash to an integer
    hash_hex = hash_object.hexdigest()[:8]
    unique_id = int(hash_hex, 16) % 1000000  # Get the remainder when divided by 1,000,000
    return str(unique_id)




