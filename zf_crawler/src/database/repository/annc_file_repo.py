# database/repository/annc_files_repository.py

from src.database.db_handler import DataBaseHandler 
from psycopg2 import extras
from typing import List, Dict, Any, Optional

class AnncFileRepository(DataBaseHandler):
    
    TABLE_NAME = "annc_files"
    
    # FILE_ID는 BIGSERIAL이므로 제외
    COLUMNS = [
        "annc_id", "file_name", "file_type", "file_path", 
        "file_ext", "file_size"
    ]

    def __init__(self):
        super().__init__()
        
    # --------------------------------------------------------------------------
    ## INSERT (파일 데이터 삽입)
    # --------------------------------------------------------------------------
    def bulk_insert_files(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        공고 파일 레코드를 대량 삽입합니다.
        :param records: 삽입할 파일 데이터 리스트 (annc_id 포함).
        :return: 삽입된 파일의 file_id와 file_name 리스트.
        """
        insert_cols_str = ', '.join(self.COLUMNS)
        placeholders = ', '.join(['%s'] * len(self.COLUMNS))
        query = f"INSERT INTO {self.TABLE_NAME} ({insert_cols_str}) VALUES ({placeholders}) RETURNING file_id, file_name"
        
        data_to_insert = [
            tuple(rec.get(col, None) for col in self.COLUMNS)
            for rec in records
        ]
            
        try:
            with self as db:
                with db.conn.cursor() as cur:
                    results = []
                    for data in data_to_insert:
                        cur.execute(query, data)
                        row = cur.fetchone()
                        results.append({'file_id': row[0], 'file_name': row[1]})
                    return results
        except Exception as e:
            print(f"ANNC_FILES 삽입 실패: {e}")
            raise

    # --------------------------------------------------------------------------
    ## SELECT (조인 조회)
    # --------------------------------------------------------------------------
    def get_files_with_announcement_info(self, annc_id: int) -> List[Dict[str, Any]]:
        """
        특정 공고 ID에 연결된 파일 목록과 공고 제목(URL)을 조인하여 조회합니다.
        """
        try:
            with self as db:
                query = f"""
                    SELECT 
                        f.*, a.annc_url, a.corp_cd 
                    FROM {self.TABLE_NAME} f
                    JOIN annc_all a ON f.annc_id = a.annc_id
                    WHERE f.annc_id = %s
                """
                return db.execute_query(query, (annc_id,), fetch_one=False)
        except Exception as e:
            print(f"ANNC_FILES 조인 조회 실패: {e}")
            raise

    # --------------------------------------------------------------------------
    ## DELETE (삭제)
    # --------------------------------------------------------------------------
    def delete_files_by_annc_id(self, annc_id: int) -> int:
        """공고 ID에 연결된 모든 파일 레코드를 삭제합니다."""
        try:
            with self as db:
                query = f"DELETE FROM {self.TABLE_NAME} WHERE annc_id = %s"
                with db.conn.cursor() as cur:
                    cur.execute(query, (annc_id,))
                    return cur.rowcount
        except Exception as e:
            print(f"ANNC_FILES 삭제 실패: {e}")
            raise