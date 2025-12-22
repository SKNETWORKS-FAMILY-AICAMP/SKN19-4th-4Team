from .db_handler import DataBaseHandler

class Initializing(DataBaseHandler):
    """
    초기화
    """
    def __init__(self):
        super().__init__()

    def set_default_tables(self, drop=False, sample_data=False):
        """기본 테이블 생성 (ANNC_LH_TEMP, ANNC_ALL, ANNC_FILES, DOC_CHUNKS)"""

        queries_execute = [
            # (설명, 테이블명, CREATE 쿼리, INSERT 쿼리)
            (
                "LH 공고 크롤링 배치",
                "ANNC_LH_TEMP",
                """
                CREATE TABLE IF NOT EXISTS ANNC_LH_TEMP (
                    BATCH_ID UUID NOT NULL, 
                    BATCH_SEQ INT NOT NULL, 
                    ANNC_URL TEXT, 
                    batch_status VARCHAR(10), 
                    BATCH_START_DTTM TIMESTAMPTZ, 
                    BATCH_END_DTTM TIMESTAMPTZ,
                    ANNC_TITLE VARCHAR(200),
                    ANNC_TYPE VARCHAR(50), 
                    ANNC_DTL_TYPE VARCHAR(20), 
                    ANNC_REGION VARCHAR(50), 
                    ANNC_PBLSH_DT VARCHAR(50), 
                    ANNC_DEADLINE_DT VARCHAR(50), 
                    ANNC_STATUS VARCHAR(20), 
                    LH_PAN_ID VARCHAR(50), 
                    LH_AIS_TP_CD VARCHAR(10), 
                    LH_UPP_AIS_TP_CD VARCHAR(10), 
                    LH_CCR_CNNT_SYS_DS_CD VARCHAR(10), 
                    LH_LS_SST VARCHAR(50), 
                    PRIMARY KEY (BATCH_ID, BATCH_SEQ)
                );
                """,
                None,
            ),
            (
                "공고 전체 테이블",
                "ANNC_ALL",
                """
                CREATE TABLE IF NOT EXISTS ANNC_ALL (
                    ANNC_ID BIGSERIAL PRIMARY KEY, 
                    ANNC_URL TEXT UNIQUE, 
                    CORP_CD VARCHAR(10), 
                    ANNC_TITLE VARCHAR(200),
                    ANNC_TYPE VARCHAR(50), 
                    ANNC_DTL_TYPE VARCHAR(20), 
                    ANNC_REGION VARCHAR(50), 
                    ANNC_PBLSH_DT VARCHAR(50), 
                    ANNC_DEADLINE_DT VARCHAR(50), 
                    ANNC_STATUS VARCHAR(20), 
                    SERVICE_STATUS VARCHAR(20)
                );
                """,
                """
                INSERT INTO ANNC_ALL (
                        ANNC_URL,
                        CORP_CD,
                        ANNC_TYPE,
                        ANNC_DTL_TYPE,
                        ANNC_REGION,
                        ANNC_PBLSH_DT,
                        ANNC_DEADLINE_DT,
                        ANNC_STATUS,
                        SERVICE_STATUS
                    )
                VALUES (
                        'http://annc.co.kr/1001',
                        'LH',
                        '주택공급',
                        '임대',
                        '전국',
                        '2025-11-01',
                        '2025-12-31',
                        '진행중',
                        'Y'
                    ) ON CONFLICT (ANNC_URL) DO NOTHING;
                """,  # 중복 삽입 방지를 위해 ON CONFLICT 추가
            ),
            (
                "공고 파일",
                "ANNC_FILES",
                """
                CREATE TABLE IF NOT EXISTS ANNC_FILES (
                    FILE_ID BIGSERIAL, 
                    ANNC_ID BIGSERIAL, 
                    FILE_NAME VARCHAR(500), 
                    FILE_TYPE VARCHAR(10), 
                    FILE_PATH VARCHAR(2000) UNIQUE, 
                    FILE_EXT VARCHAR(10), 
                    FILE_SIZE INT, 
                    PRIMARY KEY (FILE_ID, ANNC_ID), 
                    FOREIGN KEY (ANNC_ID) REFERENCES ANNC_ALL (ANNC_ID) ON DELETE CASCADE
                );
                """,
                """
                INSERT INTO ANNC_FILES (
                        ANNC_ID,
                        FILE_NAME,
                        FILE_TYPE,
                        FILE_PATH,
                        FILE_EXT,
                        FILE_SIZE
                    )
                VALUES (
                        (SELECT ANNC_ID FROM ANNC_ALL WHERE ANNC_URL = 'http://annc.co.kr/1001'),
                        '2025년 주택공급 공고문.pdf',
                        '공고',
                        '/data/annc/1/file.pdf',
                        'pdf',
                        102400
                    ) ON CONFLICT (FILE_PATH) DO NOTHING;
                """,  # ANNC_ID를 조회하여 삽입하는 방식으로 변경, 중복 삽입 방지를 위해 ON CONFLICT 추가
            ),
            (
                "공고 파일 청크 벡터",
                "DOC_CHUNKS",
                """
                CREATE TABLE IF NOT EXISTS DOC_CHUNKS (
                    CHUNK_ID BIGSERIAL, 
                    FILE_ID BIGSERIAL, 
                    ANNC_ID BIGSERIAL, 
                    CHUNK_TYPE VARCHAR(20),
                    CHUNK_TEXT TEXT, 
                    PAGE_NUM SMALLINT, 
                    EMBEDDING VECTOR(1536), 
                    METADATA JSONB, 
                    PRIMARY KEY (CHUNK_ID), -- FILE_ID, ANNC_ID를 포함하지 않도록 수정 (일반적인 VEC DB 패턴)
                    FOREIGN KEY (FILE_ID, ANNC_ID) REFERENCES ANNC_FILES (FILE_ID, ANNC_ID) ON DELETE CASCADE
                );
                """,
                None,  # 벡터 데이터 샘플은 복잡하여 주석 처리 유지
            ),
        ]

        try:
            with self as db:
                with db.conn.cursor() as cur:                
                    for title, table_name, create_query, insert_query in queries_execute:
                        
                        if drop:
                            # DROP TABLE IF EXISTS ANNC_LH_TEMP; 는 너무 구체적이므로 테이블명 변수 사용
                            cur.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
                            print(f"👎 table {title}-[{table_name}] dropped (CASCADE)")

                        cur.execute(create_query)
                        print(f"✅ table {title}-[{table_name}] created")

                        if sample_data and insert_query:
                            cur.execute(insert_query)
                            print(f"✨ table {table_name} sample data inserted")

            

        except Exception as e:
            print(f"테이블 생성 실패: {e}")
            raise

