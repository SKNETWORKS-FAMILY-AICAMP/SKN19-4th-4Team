import os
import psycopg2
from psycopg2 import extras, OperationalError
from pgvector.psycopg2 import register_vector
from typing import Optional, List, Dict, Any

# load_dotenv() 는 클래스 외부에서 실행되었다고 가정

class DataBaseHandler():
    """
    PostgreSQL 데이터베이스 연결을 관리하고 쿼리 실행을 위한 Context Manager를 제공
    """

    def __init__(self):
        # 환경 변수에서 DB 정보 로드
        self.db_host = os.getenv("DB_HOST")
        self.db_port = os.getenv("DB_PORT", "5432") # 기본값 설정
        self.db_user = os.getenv("DB_USER")
        self.db_password = os.getenv("DB_PASSWORD")
        self.db_name = os.getenv("DB_NAME")
        self.conn = None

    def __enter__(self):
        """Context Manager 시작 시 연결 설정"""
        self.make_connection()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager 종료 시 자원 정리 및 트랜잭션 처리"""
        if self.conn:
            if exc_type is None:
                # 예외가 없으면 커밋
                self.conn.commit()
            else:
                # 예외가 발생하면 롤백
                self.conn.rollback()
                # 예외를 다시 발생시켜 상위 호출자에게 알림
                raise exc_val
            
            self.conn.close()
            self.conn = None
        
    def make_connection(self):
        """DB 연결을 생성하고 pgvector를 등록"""
        if self.conn and not self.conn.closed:
            return self.conn

        try:
            self.conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
            )
            # pgvector를 등록
            register_vector(self.conn)
            
        except psycopg2.Error as e:
            # 연결 실패 시 명확하게 오류 발생
            print(f"DB 연결 실패: {e}")
            raise OperationalError(f"데이터베이스 연결 오류: {e}")

    def execute_query(self, query: str, params: Optional[tuple] = None, fetch_one: bool = False) -> List[Dict[str, Any]]:
        """
        쿼리를 실행하고 결과를 반환합니다.
        DML/DDL (fetch_one=False) 및 SELECT (fetch_one=True/False) 모두 사용 가능.
        """
        # Context Manager의 __enter__가 호출되었다고 가정 (self.conn이 존재)
        if not self.conn or self.conn.closed:
            raise OperationalError("연결이 닫혀있거나 초기화되지 않았습니다. 'with' 구문을 사용하세요.")

        try:
            # DictCursor를 사용하여 결과를 딕셔너리로 받음
            with self.conn.cursor(cursor_factory=extras.DictCursor) as cur:
                cur.execute(query, params)
                
                # SELECT 쿼리인 경우 결과 반환
                if cur.description: 
                    if fetch_one:
                        result = cur.fetchone()
                        return [dict(result)] if result else []
                    else:
                        return [dict(row) for row in cur.fetchall()]
                
                # DML/DDL (INSERT, UPDATE 등)의 경우 변경된 row 수 반환
                else:
                    print(f"쿼리 실행 완료. 영향 받은 행 수: {cur.rowcount}")
                    return []

        except psycopg2.Error as e:
            # 쿼리 실행 중 오류가 나면 롤백은 __exit__이 처리
            print(f"쿼리 실행 오류: {e}")
            raise

    

            