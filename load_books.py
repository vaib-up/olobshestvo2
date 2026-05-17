# load_books.py
# Запускать ОДИН РАЗ (или при добавлении новых PDF).
# Парсит все PDF из папки books/ и загружает в ChromaDB.

import os
import fitz  # pymupdf
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

BOOKS_DIR = "./books"
DB_DIR = "./chroma_db"

# Размер одного чанка в символах и перекрытие
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def split_text(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def parse_pdf(path: str) -> str:
    doc = fitz.open(path)
    return "\n".join(page.get_text() for page in doc)


def load_all_books():
    ef = SentenceTransformerEmbeddingFunction(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    client = chromadb.PersistentClient(path=DB_DIR)
    collection = client.get_or_create_collection(
        name="books",
        embedding_function=ef,
    )

    pdf_files = [f for f in os.listdir(BOOKS_DIR) if f.endswith(".pdf")]
    print(f"Найдено PDF: {len(pdf_files)}")

    for filename in pdf_files:
        filepath = os.path.join(BOOKS_DIR, filename)
        book_name = filename.replace(".pdf", "")

        # определяем раздел из префикса файла
        section = book_name.split("_")[0] if "_" in book_name else "general"

        print(f"  Обрабатываю: {filename} → раздел [{section}]")

        text = parse_pdf(filepath)
        chunks = split_text(text)

        ids = [f"{book_name}__{i}" for i in range(len(chunks))]
        meta = [{"book": book_name, "section": section, "chunk": i}
                for i in range(len(chunks))]

        # загружаем батчами по 100 чанков
        batch = 100
        for i in range(0, len(chunks), batch):
            collection.add(
                documents=chunks[i:i + batch],
                ids=ids[i:i + batch],
                metadatas=meta[i:i + batch],
            )
            # сохраняем сами тексты отдельно — ChromaDB хранит только id+meta

        print(f"    Чанков добавлено: {len(chunks)}")

    print("Готово! База создана в ./chroma_db")


if __name__ == "__main__":
    load_all_books()