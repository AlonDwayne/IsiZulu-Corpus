# server.py - Updated with document viewing functionality
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
import os
import uuid
import docx
import PyPDF2
import io

# Configure your DB connection
db_config = {
    "host": "localhost",
    "user": "root",        # change this
    "password": "",        # change this
    "database": "mycorpus"   # change this
}

app = FastAPI()

# Allow frontend (JS fetch) to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class SearchRequest(BaseModel):
    keyword: str

# Helper function to get database connection
def get_db_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database connection error: {err}")

# Endpoint: Get all documents
@app.get("/documents/")
def get_documents():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, title, text, genre, source FROM documents")
        docs = cursor.fetchall()
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            conn.close()

# Endpoint: Get individual document by ID
@app.get("/documents/{doc_id}")
def get_document(doc_id: int):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, title, text, genre, source FROM documents WHERE id = %s", (doc_id,))
        doc = cursor.fetchone()
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return doc
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            conn.close()

# Endpoint: Search keyword frequency
@app.post("/search/")
def search_keyword(request: SearchRequest):
    keyword = request.keyword.lower()
    conn = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT text FROM documents")
        texts = cursor.fetchall()
        
        frequency = sum(text["text"].lower().split().count(keyword) for text in texts)
        return {"keyword": keyword, "frequency": frequency}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            conn.close()

# Endpoint: Get keyword context
@app.post("/context/")
def get_context(request: SearchRequest):
    keyword = request.keyword.lower()
    conn = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, title, text, source FROM documents")
        docs = cursor.fetchall()
        
        contexts = []
        for doc in docs:
            text = doc["text"]
            lower_text = text.lower()
            pos = 0
            while (pos := lower_text.find(keyword, pos)) != -1:
                start = max(0, pos - 50)
                end = min(len(text), pos + len(keyword) + 50)
                snippet = text[start:end].replace("\n", " ")
                contexts.append({
                    "doc_id": doc["id"],
                    "title": doc["title"],
                    "source": doc["source"],
                    "context": snippet
                })
                pos += len(keyword)
        
        return contexts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            conn.close()

# Endpoint: Upload document
@app.post("/upload/")
async def upload_document(
    title: str = Form(...),
    genre: str = Form(...),
    source: str = Form(...),
    file: UploadFile = File(...)
):
    conn = None
    try:
        # Read file content based on file type
        content = ""
        if file.filename.endswith('.txt'):
            content = (await file.read()).decode('utf-8')
        elif file.filename.endswith('.docx'):
            docx_content = await file.read()
            doc = docx.Document(io.BytesIO(docx_content))
            content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        elif file.filename.endswith('.pdf'):
            pdf_content = await file.read()
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            for page in pdf_reader.pages:
                content += page.extract_text() + "\n"
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Save to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if document with same title already exists
        check_query = "SELECT id FROM documents WHERE title = %s"
        cursor.execute(check_query, (title,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Document with this title already exists")
        
        # Insert new document
        insert_query = """
        INSERT INTO documents (title, text, genre, source)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (title, content, genre, source))
        conn.commit()
        
        # Get the ID of the inserted document
        cursor.execute("SELECT LAST_INSERT_ID()")
        doc_id = cursor.fetchone()[0]
        
        return {
            "id": doc_id,
            "title": title,
            "message": "Document uploaded successfully"
        }
        
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            conn.close()

# Endpoint: Get corpus statistics
@app.get("/stats/")
def get_corpus_stats():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get total documents count
        cursor.execute("SELECT COUNT(*) as total FROM documents")
        total_docs = cursor.fetchone()["total"]
        
        # Get documents by genre
        cursor.execute("""
            SELECT genre, COUNT(*) as count 
            FROM documents 
            GROUP BY genre
        """)
        genre_stats = cursor.fetchall()
        
        # Get total word count
        cursor.execute("SELECT text FROM documents")
        texts = cursor.fetchall()
        total_words = sum(len(text["text"].split()) for text in texts)
        
        return {
            "total_documents": total_docs,
            "total_words": total_words,
            "genre_stats": genre_stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if conn and conn.is_connected():
            conn.close()

# Health check endpoint
@app.get("/health/")
def health_check():
    return {"status": "healthy", "service": "IsiZulu Corpus API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)