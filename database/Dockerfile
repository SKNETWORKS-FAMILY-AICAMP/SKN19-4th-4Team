# 사용할 기본 PostgreSQL 이미지 지정
FROM pgvector/pgvector:pg17

# 1단계에서 생성한 schema.sql 파일을 컨테이너 내부의 초기화 디렉토리에 복사
# 이 디렉토리에 있는 SQL 파일은 컨테이너 시작 시 자동으로 실행됩니다.
COPY schema.sql /docker-entrypoint-initdb.d/