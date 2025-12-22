# database/repository/doc_chunks_repository.py

from src.database.db_handler import DataBaseHandler 
from psycopg2 import extras
from typing import List, Dict, Any, Optional

class DocChunkRepository(DataBaseHandler):
    
    TABLE_NAME = "doc_chunks"
    
    # CHUNK_ID (BIGSERIAL)을 제외한 모든 컬럼
    COLUMNS = [
        "file_id", "annc_id", "chunk_type", "chunk_text", "page_num", 
        "embedding", "metadata"
    ]

    def __init__(self):
        super().__init__()
        
    # --------------------------------------------------------------------------
    ## INSERT (청크 데이터 삽입)
    # --------------------------------------------------------------------------
    def bulk_insert_chunks(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        문서 청크 데이터를 대량 삽입하고, 삽입된 청크의 ID와 ANNC_ID를 반환합니다.
        
        :param records: 삽입할 청크 데이터 리스트. (embedding은 Optional)
        :return: {chunk_id, annc_id} 딕셔너리 리스트.
        """
        insert_cols_str = ', '.join(self.COLUMNS)
        
        # 튜플 리스트로 변환
        data_to_insert = [
            tuple(rec.get(col, None) for col in self.COLUMNS)
            for rec in records
        ]
            
        try:
            with self as db:
                # DictCursor를 사용하여 결과를 딕셔너리로 받습니다.
                with db.conn.cursor(cursor_factory=extras.DictCursor) as cur:
                    values_template = f"({', '.join(['%s'] * len(self.COLUMNS))})"
                    
                    # execute_values를 사용하여 bulk insert 후 RETURNING으로 ID를 가져옵니다.
                    extras.execute_values(
                        cur,
                        f"""
                            INSERT INTO {self.TABLE_NAME} ({insert_cols_str}) 
                            VALUES %s
                            RETURNING chunk_id, annc_id;  
                        """,
                        data_to_insert,
                        template=values_template
                    )
                    
                    results = [dict(row) for row in cur.fetchall()]
                    return results
                    
        except Exception as e:
            print(f"DOC_CHUNKS 삽입 실패: {e}")
            raise

    def bulk_update_embeddings(self, updates: List[Dict[str, Any]]) -> int:
        """
        주어진 CHUNK_ID 목록을 기반으로 임베딩 벡터를 갱신합니다. (BULK)
        
        :param updates: 갱신할 데이터 딕셔너리 리스트. 
                        (필수 키: 'chunk_id', 'embedding'. 선택 키: 'metadata')
        :return: 갱신된 행의 총 개수.
        """
        # UPDATE 쿼리 (CHUNK_ID를 키로 사용)
        query = f"""
            UPDATE {self.TABLE_NAME}
            SET embedding = %s,
                metadata = %s
            WHERE chunk_id = %s
        """
        
        # 튜플 리스트로 변환: (embedding, metadata, chunk_id) 순서
        data_to_update = []
        for rec in updates:
            chunk_id = rec.get("chunk_id")
            embedding = rec.get("embedding")
            metadata = rec.get("metadata")
            
            # chunk_id와 embedding이 없으면 갱신할 수 없습니다.
            if embedding is None or chunk_id is None:
                continue 
            
            data_to_update.append((embedding, metadata, chunk_id))
            
        if not data_to_update:
            return 0
            
        try:
            with self as db:
                with db.conn.cursor() as cur:
                    # execute_batch를 사용하여 대량 갱신 실행
                    extras.execute_batch(cur, query, data_to_update)
                    return cur.rowcount
        except Exception as e:
            print(f"DOC_CHUNKS 임베딩 갱신 실패: {e}")
            raise

    # --------------------------------------------------------------------------
    ## SELECT (벡터 유사도 검색)
    # --------------------------------------------------------------------------
    def search_by_vector_similarity(self, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """
        쿼리 벡터와 가장 유사한 청크를 코사인 유사도(L2 distance)를 사용하여 검색합니다.
        (pgvector의 L2 distance 연산자 <-> 사용)
        """
        try:
            with self as db:
                # <-> 연산자는 L2 distance를 측정. ORDER BY를 통해 가장 작은 값이 가장 유사한 벡터입니다.
                query = f"""
                    SELECT chunk_text, page_num, annc_id, file_id, embedding <-> %s AS distance
                    FROM {self.TABLE_NAME}
                    ORDER BY distance
                    LIMIT %s
                """
                params = (query_vector, limit)
                return db.execute_query(query, params, fetch_one=False)
        except Exception as e:
            print(f"벡터 유사도 검색 실패: {e}")
            raise

    # --------------------------------------------------------------------------
    ## DELETE (삭제)
    # --------------------------------------------------------------------------
    def delete_chunks_by_annc_id(self, annc_id: int) -> int:
        """공고 ID에 연결된 모든 청크 레코드를 삭제합니다."""
        try:
            with self as db:
                query = f"DELETE FROM {self.TABLE_NAME} WHERE annc_id = %s"
                with db.conn.cursor() as cur:
                    cur.execute(query, (annc_id,))
                    return cur.rowcount
        except Exception as e:
            print(f"DOC_CHUNKS 삭제 실패: {e}")
            raise