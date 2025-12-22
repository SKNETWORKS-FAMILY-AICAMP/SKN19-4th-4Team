# database/repository/annc_lh_repository.py

import uuid
import datetime
from psycopg2 import extras
from typing import List, Dict, Any, Optional

# 상위 모듈에서 DataBaseHandler Base 클래스를 임`포트
# (from ..db_handler import DataBaseHandler 도 가능하지만, 
#  현재 __init__.py 설정을 고려하여 from database import DataBaseHandler로 가정)
from src.database.db_handler import DataBaseHandler 


class AnncLhRepository(DataBaseHandler):
    """
    Announce LH Repository
    ANNC_LH_TEMP 테이블 관련 데이터 접근 로직을 전담합니다.
    """
    
    TABLE_NAME = "annc_lh_temp"
    COLUMNS = [
        "batch_id", "batch_seq", "annc_title", "annc_url", "batch_status", "batch_start_dttm", 
        "annc_type", "annc_dtl_type", "annc_region", "annc_pblsh_dt", 
        "annc_deadline_dt", "annc_status", "lh_pan_id", "lh_ais_tp_cd", 
        "lh_upp_ais_tp_cd", "lh_ccr_cnnt_sys_ds_cd", "lh_ls_sst"
    ]

    def __init__(self):
        super().__init__()
        
    # --------------------------------------------------------------------------
    ## 1. Bulk Insert (대량 삽입) - 성능 최적화 핵심
    # --------------------------------------------------------------------------
    def bulk_insert_announcements(self, records: List[Dict[str, Any]]) -> int:
        """
        psycopg2.extras.execute_batch를 사용하여 여러 공고 데이터를 대량 삽입합니다.

        :param records: 삽입할 데이터 딕셔너리 리스트.
        :return: 삽입된 행의 총 개수.
        """
        # BATCH_ID는 모든 레코드에서 동일한 UUID를 사용
        batch_id = str(uuid.uuid4())
        current_time = datetime.datetime.now(datetime.timezone.utc)
        
        # 삽입할 컬럼 목록 (BATCH_SEQ는 SERIAL이므로 제외)       
        
        query = f"""
            insert into {self.TABLE_NAME} ({', '.join(self.COLUMNS)})
            values ({', '.join(['%s'] * len(self.COLUMNS))})
        """
        
        data_to_insert = []
        for i, rec in enumerate(records):
            # 쿼리의 컬럼 순서에 맞게 데이터 튜플 생성
            row = (
                batch_id,
                i+1,
                rec.get("annc_title"),
                rec.get("annc_url"),
                rec.get("batch_status", "PENDING"),
                current_time, 
                rec.get("annc_type"),
                rec.get("annc_dtl_type"),
                rec.get("annc_region"),
                rec.get("annc_pblsh_dt"),
                rec.get("annc_deadline_dt"),
                rec.get("annc_status"),
                rec.get("lh_pan_id"),
                rec.get("lh_ais_tp_cd"),
                rec.get("lh_upp_ais_tp_cd"),
                rec.get("lh_ccr_cnnt_sys_ds_cd"),
                rec.get("lh_ls_sst"),
            )
            data_to_insert.append(row)

        # print(query)
        # print(data_to_insert)
            
        try:
            with self as db:
                # execute_batch는 기본 커서를 사용
                with db.conn.cursor() as cur:
                    extras.execute_batch(cur, query, data_to_insert)
                    row_count = cur.rowcount
                    return batch_id
        except Exception as e:
            print(f"Bulk Insert 실패: {e}")
            raise


    # --------------------------------------------------------------------------
    ## 2. Select (조건부 조회)
    # --------------------------------------------------------------------------
    def get_announcements(
            self,
            batch_id: str,
            batch_status: Optional[str] = None,
            annc_type: Optional[str]|Optional[List] = None,
            annc_status: Optional[str] = None
            ) -> List[Dict[str, Any]]:
        """
        특정 BATCH_STATUS를 가진 공고 목록을 조회합니다.
        """
        try:
            with self as db:
                
                if type(annc_type) == str:
                    annc_type_list = (annc_type,)
                elif type(annc_type) == list:
                    annc_type_list = tuple(annc_type)
                elif type(annc_type) == tuple:
                    annc_type_list = annc_type
                else:
                    annc_type_list = None

                query = f"""
                    select * from {self.TABLE_NAME} 
                    where (%s is null or "batch_id" = %s)
                    and (%s is null or "batch_status" = %s)
                    and (%s is null or "annc_type" in %s)
                    and (%s is null or "annc_status" = %s)
                    order by "batch_seq" asc
                """
                params = (
                    batch_id, batch_id,
                    batch_status, batch_status,
                    annc_type, tuple(annc_type_list),
                    annc_status, annc_status,
                )
                
                # 부모 클래스의 execute_query를 재사용 (DictCursor로 결과 반환)
                return db.execute_query(query, params, fetch_one=False)
        except Exception as e:
            print(f"공고 조회 실패: {e}")
            raise


    # --------------------------------------------------------------------------
    ## 3. Delete (조건부 삭제)
    # --------------------------------------------------------------------------
    def delete_announcements_by_batch_id(self, batch_id: str) -> int:
        """
        특정 BATCH_ID를 가진 모든 공고를 삭제합니다.
        
        :param batch_id: 삭제할 레코드의 배치 ID (UUID 문자열).
        :return: 삭제된 행의 개수. (execute_query 반환값 수정 필요)
        """
        try:
            with self as db:
                query = f"""
                    delete from {self.TABLE_NAME} 
                    where "batch_id" = %s
                """
                params = (batch_id,)
                
                # execute_query는 DML 실행 후 현재는 빈 리스트를 반환하고,
                # rowcount는 출력만 하고 있으므로, execute_query를 수정하거나
                # 이 메서드 내에서 커서를 직접 사용하여 rowcount를 가져와야 합니다.
                
                # 임시로 커서를 직접 사용하여 rowcount를 반환하도록 수정
                with db.conn.cursor() as cur:
                    cur.execute(query, params)
                    return cur.rowcount
                
        except Exception as e:
            print(f"공고 삭제 실패: {e}")
            raise

    # --------------------------------------------------------------------------
    ## 4. Update (조건부 수정)
    # --------------------------------------------------------------------------
    def update_announcements(self, batch_status: str, batch_id: str, batch_seq: tuple|list|int):
        """
        batch_id, batch_seq_list로 batch_status를 갱신합니다.
        batch_status가 'COMPLETE'인 경우 batch_end_dttm도 현재 시간으로 설정합니다.
        """
        try:

            if type(batch_seq) == int:
                batch_seq_list = (batch_seq,)
            elif type(batch_seq) == list:
                batch_seq_list = tuple(batch_seq)
            elif type(batch_seq) == tuple:
                batch_seq_list = batch_seq
            else:
                batch_seq_list = None

            with self as db:
                if batch_status == 'COMPLETE':
                    current_time = datetime.datetime.now(datetime.timezone.utc)
                    query = f"""
                        update {self.TABLE_NAME}
                        set batch_status = %s,
                            batch_end_dttm = %s
                        where batch_id = %s
                        and batch_seq in %s
                    """
                    params = (batch_status, current_time, batch_id, batch_seq_list)
                else:
                    query = f"""
                        update {self.TABLE_NAME}
                        set batch_status = %s
                        where batch_id = %s
                        and batch_seq in %s
                    """
                    params = (batch_status, batch_id, batch_seq_list)

                with db.conn.cursor() as cur:
                    cur.execute(query, params)
                    return cur.rowcount
        except Exception as e:
            print(f"공고 삭제 실패: {e}")
            raise