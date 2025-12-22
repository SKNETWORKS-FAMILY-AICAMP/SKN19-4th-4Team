import datetime
from psycopg2 import extras
from typing import List, Dict, Any, Optional
from ...utils import strip_particles

# 상위 모듈에서 DataBaseHandler Base 클래스를 임`포트
# (from ..db_handler import DataBaseHandler 도 가능하지만, 
#  현재 __init__.py 설정을 고려하여 from database import DataBaseHandler로 가정)
from src.database.db_handler import DataBaseHandler 


class AnncQrRepository(DataBaseHandler):
    TABLE_NAME_LH_TEMP = "annc_lh_temp"
    TABLE_NAME_ANNC_ALL = "annc_all"
    TABLE_NAME_DOC_CHUNKS = "doc_chunks"
    COLUMNS_ANNC_ALL = [
        'annc_id','annc_title','annc_url',
        'corp_cd',
        'annc_type','annc_dtl_type',
        'annc_pblsh_dt','annc_deadline_dt',
        'annc_status','service_status'
    ]
    COLUMNS_LH_TEMP = [
        "batch_id", "batch_seq",'annc_title', "annc_url", "batch_status", "batch_start_dttm", 
        "annc_type", "annc_dtl_type", "annc_region",
        "annc_pblsh_dt", "annc_deadline_dt",
        "annc_status", "lh_pan_id", "lh_ais_tp_cd", 
        "lh_upp_ais_tp_cd", "lh_ccr_cnnt_sys_ds_cd", "lh_ls_sst"
    ]
    COLUMNS_JOINED = [
        "batch_id", "batch_seq", 'annc_title', "annc_url", "batch_status", "batch_start_dttm", 
        "annc_type", "annc_dtl_type", "annc_region",
        "annc_pblsh_dt", "annc_deadline_dt",
        "annc_status", "lh_pan_id", "lh_ais_tp_cd", 
        "lh_upp_ais_tp_cd", "lh_ccr_cnnt_sys_ds_cd", "lh_ls_sst"
    ]

    def __init__(self):
        super().__init__()

    def get_announcements_merge_target(self, batch_id: str, annc_type_list: tuple|list=('임대','분양'), annc_status: Optional[str|tuple|list]=None):


        try:
            with self as db:

                if type(annc_status) == str:
                    # print("annc_type = str")
                    annc_status_list = (annc_status,)
                elif type(annc_status) == list:
                    # print("annc_type = List")
                    annc_status_list = tuple(annc_status)
                elif type(annc_status) == tuple:
                    # print("annc_type = tuple")
                    annc_status_list = annc_status
                else:
                    annc_status_list = None

                temp_columns = ','.join(['alt.' + col_name for col_name in self.COLUMNS_LH_TEMP])
                return_columns = ','.join(['alt.' + col_name for col_name in self.COLUMNS_JOINED])

                sql_query = f"""
                    select distinct {return_columns}
                    from (
                        select {temp_columns}
                        from {self.TABLE_NAME_LH_TEMP} alt
                        where alt.batch_id = %s
                            and not exists(
                                select *
                                from {self.TABLE_NAME_ANNC_ALL} aa
                                where aa.annc_url = alt.annc_url
                            )
                            and alt.annc_type in %s
                            and (%s is null or alt.annc_status in %s)
                        union all
                        select {temp_columns}
                        from {self.TABLE_NAME_LH_TEMP} alt
                            join {self.TABLE_NAME_ANNC_ALL} aa on alt.annc_url = aa.annc_url
                        where alt.batch_id = %s
                            and (alt.annc_pblsh_dt != aa.annc_pblsh_dt
                            or alt.annc_deadline_dt != aa.annc_deadline_dt
                            or alt.annc_status != aa.annc_status
                            or aa.service_status != 'OPEN')
                            and alt.annc_type in %s
                            and (%s is null or alt.annc_status in %s)
                            
                    ) alt
                    where batch_status not in ('COMPLETE')
                    order by alt.batch_seq asc;
                """
                params = (
                    batch_id, tuple(annc_type_list), annc_status_list, annc_status_list,
                    batch_id, tuple(annc_type_list), annc_status_list, annc_status_list
                )

                # print(sql_query)
                return db.execute_query(sql_query, params, fetch_one=False)
        except Exception as e:
            print(f"공고 조회 실패: {e}")
            raise

        

    def hybrid_search(self, query: str, query_embedding: List[float], top_k: int = 10, k: int = 60):
        """하이브리드 검색 (키워드 + 벡터) + RRF 재정렬

        특정 공고가 매칭되면 해당 공고의 청크도 함께 반환
        """
        with self as db:
            words = query.split()
            # 조사 제거된 키워드 (검색용)
            clean_words = [strip_particles(w) for w in words if len(w) >= 2]
            clean_words = [w for w in clean_words if len(w) >= 2]

            # 1단계: 공고 title 매칭 - 1개 이상 단어가 매칭되는 공고
            like_patterns = [f"%{w}%" for w in clean_words]
            matched_ann_ids: list[int] = []
            if like_patterns:
                sql_ann = f"""
                    SELECT annc_id
                    FROM {self.TABLE_NAME_ANNC_ALL}
                    WHERE {' OR '.join(['annc_title LIKE %s' for _ in like_patterns])}
                """
                ann_rows = db.execute_query(sql_ann, tuple(like_patterns), fetch_one=False)
                matched_ann_ids = [r["annc_id"] for r in ann_rows]

            # 2단계: FTS 검색 (doc_chunks 기준)
            fts_query = ' | '.join(words + [''.join(words)])
            sql_fts = f"""
                SELECT chunk_id, ts_rank(fts_vector, to_tsquery('simple', %s)) AS score
                FROM {self.TABLE_NAME_DOC_CHUNKS}
                WHERE fts_vector @@ to_tsquery('simple', %s)
                ORDER BY score DESC
                LIMIT 100;
            """
            fts_rows = db.execute_query(sql_fts, (fts_query, fts_query), fetch_one=False)
            fts_results = {row["chunk_id"]: i + 1 for i, row in enumerate(fts_rows)}

            # 3단계: 벡터 검색
            sql_vec = f"""
                SELECT chunk_id
                FROM {self.TABLE_NAME_DOC_CHUNKS}
                ORDER BY embedding <=> %s::vector
                LIMIT 100;
            """
            vec_rows = db.execute_query(sql_vec, (query_embedding,), fetch_one=False)
            vec_results = {row["chunk_id"]: i + 1 for i, row in enumerate(vec_rows)}

            # RRF 스코어 계산
            all_ids = set(fts_results) | set(vec_results)
            if not all_ids:
                return []

            rrf = {
                chunk_id: 1.0 / (k + fts_results.get(chunk_id, 1000))
                        + 1.0 / (k + vec_results.get(chunk_id, 1000))
                for chunk_id in all_ids
            }
            top_ids = [chunk_id for chunk_id, _ in sorted(rrf.items(), key=lambda x: x[1], reverse=True)[:top_k]]

            # 4단계: 매칭된 공고의 테이블 청크 추가 (키워드 + 벡터 검색)
            if matched_ann_ids:
                keyword_like = [f"%{w}%" for w in clean_words]
                if keyword_like:
                    like_conditions = ' OR '.join(['chunk_text LIKE %s' for _ in keyword_like])
                    sql_kw_table = f"""
                        SELECT chunk_id
                        FROM {self.TABLE_NAME_DOC_CHUNKS}
                        WHERE annc_id = ANY(%s)
                        AND chunk_type = 'table'
                        AND ({like_conditions})
                        LIMIT 15;
                    """
                    params_kw = (matched_ann_ids, *keyword_like)
                    kw_rows = db.execute_query(sql_kw_table, params_kw, fetch_one=False)
                    keyword_table_ids = [r["chunk_id"] for r in kw_rows]
                else:
                    keyword_table_ids = []

                # 벡터 유사도 기반 테이블 보완
                sql_vec_table = f"""
                    SELECT chunk_id
                    FROM {self.TABLE_NAME_DOC_CHUNKS}
                    WHERE annc_id = ANY(%s)
                    AND chunk_type = 'table'
                    ORDER BY embedding <=> %s::vector
                    LIMIT 10;
                """
                vec_table_rows = db.execute_query(sql_vec_table, (matched_ann_ids, query_embedding), fetch_one=False)
                vector_table_ids = [r["chunk_id"] for r in vec_table_rows]

                # 키워드 우선 + 벡터 보완 (최대 20개)
                table_ids = list(dict.fromkeys(keyword_table_ids + vector_table_ids))[:20]
                top_ids = list(dict.fromkeys(top_ids + table_ids))

            if not top_ids:
                return []

            # 최종 결과 조회
            sql_final = f"""
                SELECT
                    dc.chunk_id,
                    dc.chunk_text,
                    dc.chunk_type,
                    dc.page_num,
                    a.annc_id,
                    a.annc_title,
                    a.annc_region,
                    a.annc_type,
                    a.annc_dtl_type,
                    1 - (dc.embedding <=> %s::vector) AS similarity
                FROM {self.TABLE_NAME_DOC_CHUNKS} dc
                JOIN {self.TABLE_NAME_ANNC_ALL} a
                ON dc.annc_id = a.annc_id
                WHERE dc.chunk_id = ANY(%s)
                ORDER BY array_position(%s::bigint[], dc.chunk_id);
            """
            final_rows = db.execute_query(sql_final, (query_embedding, top_ids, top_ids), fetch_one=False)
            return final_rows
