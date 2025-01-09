# Akasha Service

Akasha Service is a document processing and retrieval service built using FastAPI. It supports uploading documents, processing them into vector databases, and retrieving relevant documents based on search queries.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/your-repo/akasha_service.git
    cd akasha_service
    ```

2. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

3. Configure the application by editing the `config.py` file with your settings.

## Usage

### Running the Service

Start the FastAPI server:
```sh
uvicorn app.main:app --host 0.0.0.0 --port 8006
```

### API Endpoints

#### Process Documents

Upload and process documents:
```sh
POST /processing_docs
```
- **Parameters**: 
  - `files`: List of files to upload.
  - `kdb_id`: Knowledge database ID (default: "default").

#### Retrieve Documents

Retrieve documents based on a search query:
```sh
POST /retriever_docs
```
- **Parameters**:
  - `text`: Search query.
  - `kdb_id`: Knowledge database ID.

#### Delete Documents

Delete specific documents:
```sh
DELETE /delete_docs
```
- **Parameters**:
  - `id`: Document ID.
  - `kdb_id`: Knowledge database ID.

#### Delete Collection

Delete an entire collection:
```sh
DELETE /delete_collection
```
- **Parameters**:
  - `kdb_id`: Knowledge database ID.

#### Get Summary

Get a summary of text content:
```sh
POST /get_summary
```
- **Parameters**:
  - `text`: Text content to summarize.

## License

This project is licensed under the MIT License.
