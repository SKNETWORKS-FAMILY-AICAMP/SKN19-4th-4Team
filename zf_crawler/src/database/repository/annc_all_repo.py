import datetime
from psycopg2 import extras
from typing import List, Dict, Any, Optional

# 상위 모듈에서 DataBaseHandler Base 클래스를 임`포트
# (from ..db_handler import DataBaseHandler 도 가능하지만, 
#  현재 __init__.py 설정을 고려하여 from database import DataBaseHandler로 가정)
from src.database.db_handler import DataBaseHandler 


class AnncAllRepository(DataBaseHandler):

    TABLE_NAME = 'annc_all'
    COLUMNS = [
        'annc_id',
        'annc_title',
        'annc_url',
        'created_at',
        'updated_at',
        'corp_cd',
        'annc_type',
        'annc_dtl_type',
        'annc_region',
        'annc_pblsh_dt',
        'annc_deadline_dt',
        'annc_status',
        'service_status'
    ]

    COLUMNS_FOR_MERGE = [
        'annc_title',
        'annc_url',
        'created_at',
        'updated_at',
        'corp_cd',
        'annc_type',
        'annc_dtl_type',
        'annc_region',
        'annc_pblsh_dt',
        'annc_deadline_dt',
        'annc_status',
        'service_status'
    ]

    def __init__(self):
        super().__init__()
        
    # --------------------------------------------------------------------------
    ## 1. MERGE (UPSERT) - Insert / Update
    # --------------------------------------------------------------------------
    def merge_announcements(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        ANNC_URL을 Unique Key로 사용하여 공고 데이터를 병합(UPSERT)하고,
        삽입 또는 갱신된 레코드의 ANNC_ID와 ANNC_URL을 반환합니다.
        """
        # INSERT 에 사용할 컬럼: updated_at 제외
        insert_cols = [col for col in self.COLUMNS_FOR_MERGE]
        # insert_cols = [col for col in self.COLUMNS_FOR_MERGE if col != 'updated_at']
        insert_cols_str = ', '.join(insert_cols)

        # UPDATE 에 사용할 컬럼: annc_url 제외 (conflict key는 update 불가)
        update_cols = [
            col for col in self.COLUMNS_FOR_MERGE
            if col not in ('annc_url','created_at')
        ]
        update_set_clauses = ', '.join(
            f"{col} = EXCLUDED.{col}"
            for col in update_cols
        )

        # execute_values 에 들어갈 데이터 튜플: INSERT 컬럼 순서와 맞춰야 함
        data_to_insert = [
            tuple(rec.get(col, None) for col in insert_cols)
            for rec in records
        ]

        print(data_to_insert)

        try:
            with self as db:
                with db.conn.cursor(cursor_factory=extras.DictCursor) as cur:
                    values_template = f"({', '.join(['%s'] * len(insert_cols))})"

                    extras.execute_values(
                        cur,
                        f"""
                            INSERT INTO {self.TABLE_NAME} ({insert_cols_str})
                            VALUES %s
                            ON CONFLICT (annc_url) DO UPDATE
                            SET {update_set_clauses}
                            RETURNING annc_id, annc_url;
                        """,
                        data_to_insert,
                        template=values_template,
                    )

                    results = [dict(row) for row in cur.fetchall()]
                    return results

        except Exception as e:
            print(f"Merge(UPSERT) 실패: {e}")
            raise

    # --------------------------------------------------------------------------
    ## 2. SELECT (조회)
    # --------------------------------------------------------------------------
    def get_announcements_by_type_and_status(
            self, 
            annc_type: Optional[str] = None, 
            service_status: Optional[str] = 'ACTV'
            ) -> List[Dict[str, Any]]:
        """
        공고 유형과 서비스 상태를 기준으로 공고 목록을 조회합니다.
        (서비스 상태의 기본값은 'ACTV' (활성화)로 가정)
        """
        try:
            with self as db:
                # 동적 WHERE 절 구성을 위한 기본 쿼리
                base_query = f"""
                    SELECT * FROM {self.TABLE_NAME} 
                    WHERE 1=1 
                """
                where_clauses = []
                params = []

                # 조건부 쿼리 구성
                if annc_type:
                    where_clauses.append(" annc_type = %s")
                    params.append(annc_type)
                
                # service_status는 기본값을 가지고 있으므로 항상 조건에 포함
                where_clauses.append(" service_status = %s")
                params.append(service_status)
                
                # WHERE 절 통합
                if where_clauses:
                    final_query = base_query + " AND ".join(where_clauses) + " ORDER BY annc_id DESC"
                else:
                    final_query = base_query + " ORDER BY annc_id DESC" # 모든 공고 조회

                # 부모 클래스의 execute_query를 재사용
                return db.execute_query(final_query, tuple(params), fetch_one=False)
        except Exception as e:
            print(f"공고 조회 실패: {e}")
            raise


    # --------------------------------------------------------------------------
    ## 3. DELETE (삭제)
    # --------------------------------------------------------------------------
    def delete_announcement_by_url(self, annc_url: str) -> int:
        """
        ANNC_URL을 기반으로 특정 공고를 삭제합니다.
        
        :param annc_url: 삭제할 공고의 URL.
        :return: 삭제된 행의 개수.
        """
        try:
            with self as db:
                query = f"""
                    DELETE FROM {self.TABLE_NAME} 
                    WHERE annc_url = %s
                """
                params = (annc_url,)
                
                # 직접 커서를 사용하여 rowcount 반환
                with db.conn.cursor() as cur:
                    cur.execute(query, params)
                    return cur.rowcount
                
        except Exception as e:
            print(f"공고 삭제 실패: {e}")
            raise