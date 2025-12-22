/**
 * API 호출 유틸리티 함수
 * 
 * user_key와 session_id는 프론트엔드에서 관리합니다.
 * - user_key: localStorage에 저장 (브라우저별로 유지)
 * - session_id: sessionStorage에 저장 (탭별로 유지)
 * 
 * 참고: Mock 데이터 사용 시 mockData.js 파일을 먼저 로드해야 합니다.
 */

// ============================================
// user_key 관리
// ============================================

/**
 * user_key 생성 또는 가져오기
 * 
 * TODO: API에서 user_key 생성 엔드포인트 확인 필요
 * 현재는 프론트엔드에서 생성하는 방식 사용
 */
function getOrCreateUserKey() {
    let userKey = localStorage.getItem('user_key');
    
    if (!userKey) {
        // API에서 생성하는 경우 여기서 호출
        // 또는 프론트엔드에서 생성
        userKey = generateUserKey();
        localStorage.setItem('user_key', userKey);
    }
    
    return userKey;
}

/**
 * user_key 생성 (프론트엔드 방식)
 *
 * TODO: API에서 생성하는 방식으로 변경 가능
 */
function generateUserKey() {
    // 10,000가지 조합 방식 (100 × 100)
    const adjectives = [
        // 1-20: 맛/향 관련
        '매콤한', '달콤한', '상쾌한', '싱그러운', '향긋한',
        '고소한', '새콤한', '짭짤한', '쌉싸름한', '담백한',
        '진한', '순한', '부드러운', '깔끔한', '산뜻한',
        '시원한', '따뜻한', '뜨거운', '차가운', '미지근한',

        // 21-40: 성격 관련
        '용감한', '귀여운', '똑똑한', '빠른', '차분한',
        '명랑한', '활발한', '조용한', '친절한', '멋진',
        '훌륭한', '당당한', '부지런한', '성실한', '밝은',
        '유쾌한', '쾌활한', '온화한', '겸손한', '대담한',

        // 41-60: 감정/느낌
        '행복한', '즐거운', '기쁜', '평화로운', '편안한',
        '고요한', '신나는', '설레는', '두근거리는', '흥분한',
        '열정적인', '적극적인', '긍정적인', '희망찬', '낙천적인',
        '여유로운', '느긋한', '태평한', '넉넉한', '푸근한',

        // 61-80: 외모/특징
        '화사한', '빛나는', '반짝이는', '투명한', '맑은',
        '선명한', '흐릿한', '뿌연', '탁한', '깨끗한',
        '더러운', '지저분한', '단정한', '깔끔한', '세련된',
        '우아한', '고급스러운', '화려한', '수수한', '소박한',

        // 81-100: 기타
        '신비로운', '환상적인', '몽환적인', '아름다운', '예쁜',
        '잘생긴', '귀엽둥이', '사랑스러운', '애교있는', '장난스러운',
        '익살스러운', '재치있는', '슬기로운', '영리한', '현명한',
        '지혜로운', '박식한', '능숙한', '숙련된', '노련한'
    ];

    const animals = [
        // 1-20: 포유류 (애완동물)
        '고양이', '강아지', '토끼', '햄스터', '다람쥐',
        '기니피그', '페럿', '친칠라', '고슴도치', '슈가글라이더',
        '미니돼지', '염소', '양', '알파카', '라마',
        '미어캣', '프레리도그', '치와와', '포메라니안', '말티즈',

        // 21-40: 야생 포유류
        '사자', '호랑이', '표범', '치타', '재규어',
        '퓨마', '스라소니', '오셀롯', '곰', '판다',
        '코알라', '캥거루', '왈라비', '웜뱃', '주머니쥐',
        '여우', '늑대', '코요테', '자칼', '하이에나',

        // 41-60: 조류
        '펭귄', '부엉이', '독수리', '매', '솔개',
        '까마귀', '까치', '참새', '비둘기', '앵무새',
        '잉꼬', '카나리아', '십자매', '문조', '금화조',
        '공작', '타조', '에뮤', '키위', '두루미',

        // 61-80: 수중 생물
        '돌고래', '고래', '상어', '물개', '바다표범',
        '해달', '수달', '비버', '해마', '불가사리',
        '해파리', '오징어', '문어', '갑오징어', '새우',
        '게', '가재', '랍스터', '전복', '소라',

        // 81-100: 기타 동물
        '사슴', '숫사슴', '순록', '무스', '엘크',
        '기린', '코끼리', '하마', '코뿔소', '얼룩말',
        '낙타', '드로메다리', '들소', '야크', '버팔로',
        '이구아나', '카멜레온', '도마뱀', '거북이', '악어'
    ];

    const adjective = adjectives[Math.floor(Math.random() * adjectives.length)];
    const animal = animals[Math.floor(Math.random() * animals.length)];

    return `${adjective} ${animal}`;
}

// ============================================
// session_id 관리
// ============================================

/**
 * session_id 생성 (새 채팅 시작 시)
 */
function createSessionId() {
    // UUID v4 생성
    const sessionId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
    
    sessionStorage.setItem('current_session_id', sessionId);
    return sessionId;
}

/**
 * 현재 session_id 가져오기
 */
function getCurrentSessionId() {
    return sessionStorage.getItem('current_session_id');
}

/**
 * session_id 설정 (기존 채팅 불러올 때)
 */
function setSessionId(sessionId) {
    sessionStorage.setItem('current_session_id', sessionId);
}

// ============================================
// API 호출 함수
// ============================================

/**
 * CSRF 토큰 가져오기
 */
function getCsrfToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
}

/**
 * 채팅 메시지 전송 및 AI 응답 받기
 *
 * @param {string} userMessage - 사용자 메시지
 * @param {string} userKey - 사용자 키 (선택사항, 없으면 자동 생성)
 * @param {string} sessionId - 세션 ID (선택사항, 없으면 자동 생성)
 * @param {Object} userProfile - 사용자 프로필 정보 (선택사항)
 * @param {string} announcementId - 공고 ID (선택사항, 공고 관련 상담 시 사용)
 * @returns {Promise<Object>} API 응답 데이터
 */
async function sendChatMessage(userMessage, userKey = null, sessionId = null, userProfile = null, announcementId = null) {
    const finalUserKey = userKey || getOrCreateUserKey();
    const finalSessionId = sessionId || getCurrentSessionId() || createSessionId();

    // 요청 데이터 구성
    const requestData = {
        user_key: finalUserKey,
        session_id: finalSessionId,
        user_message: userMessage
    };

    // 사용자 프로필 정보 추가 (있는 경우)
    if (userProfile && typeof userProfile === 'object') {
        Object.assign(requestData, userProfile);
    }

    // 공고 ID 추가 (있는 경우)
    if (announcementId) {
        requestData.announcement_id = announcementId;
    }

    const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(requestData)
    });

    if (!response.ok) {
        throw new Error(`API 호출 실패: ${response.status}`);
    }

    const data = await response.json();

    // 개발용: 응답 저장 (선택사항)
    if (window.DEBUG_MODE) {
        console.log('API 응답:', data);
    }

    return data;
}

/**
 * 채팅 히스토리 목록 조회
 * 
 * @param {string} userKey - 사용자 키 (선택사항)
 * @returns {Promise<Array>} 채팅 히스토리 목록
 */
async function getChatHistories(userKey = null) {
    const finalUserKey = userKey || getOrCreateUserKey();
    
    const response = await fetch(`/api/chathistories?user_key=${encodeURIComponent(finalUserKey)}`);
    
    if (!response.ok) {
        throw new Error(`API 호출 실패: ${response.status}`);
    }
    
    const data = await response.json();
    return data.data || [];
}

/**
 * 특정 채팅 히스토리 상세 조회
 *
 * @param {string} sessionId - 세션 ID
 * @param {string} userKey - 사용자 키 (선택사항)
 * @returns {Promise<Object>} 채팅 히스토리 상세 데이터
 */
async function getChatHistoryDetail(sessionId, userKey = null) {
    const finalUserKey = userKey || getOrCreateUserKey();

    const response = await fetch(
        `/api/chathistories/${encodeURIComponent(sessionId)}?user_key=${encodeURIComponent(finalUserKey)}`
    );

    if (!response.ok) {
        throw new Error(`API 호출 실패: ${response.status}`);
    }

    const data = await response.json();
    return data.data || {};
}

/**
 * 특정 채팅 히스토리 삭제
 *
 * @param {string} sessionId - 삭제할 세션 ID
 * @param {string} userKey - 사용자 키 (선택사항)
 * @returns {Promise<Object>} 삭제 결과 데이터
 */
async function deleteChatHistory(sessionId, userKey = null) {
    const finalUserKey = userKey || getOrCreateUserKey();

    const response = await fetch(
        `/api/chathistories/${encodeURIComponent(sessionId)}?user_key=${encodeURIComponent(finalUserKey)}`,
        {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        }
    );

    // 204 No Content는 본문이 없으므로 바로 종료
    if (response.status === 204) {
        return null;
    }

    if (!response.ok) {
        throw new Error(`API 호출 실패: ${response.status}`);
    }

    return await response.json();
}

/**
 * 공고 목록 조회
 * 
 * @param {Object} params - 조회 파라미터
 * @returns {Promise<Object>} 공고 목록 데이터
 */
async function getAnnouncements(params = {}) {
    const {
        annc_title = '',
        annc_status = '전체',
        annc_type = '전체',
        agency = '전체',  // 기관 필터 파라미터 추가
        items_per_page = 10,
        current_page = 1
    } = params;
    
    const queryParams = new URLSearchParams({
        annc_title,
        items_per_page: items_per_page.toString(),
        current_page: current_page.toString()
    });
    
    // annc_status 파라미터 추가 (전체가 아닌 경우만)
    // 주의: 상태 필터링은 클라이언트 사이드에서 동적 상태 계산 후 필터링하므로
    // 백엔드에서는 필터링하지 않음 (하위 호환성을 위해 파라미터는 전달)
    if (annc_status && annc_status !== '전체' && annc_status !== '') {
        queryParams.append('annc_status', annc_status);
    }
    
    // annc_type 파라미터 추가 (전체가 아닌 경우만)
    // 주의: 유형 필터링은 클라이언트 사이드에서 annc_dtl_type을 고려하여 필터링하므로
    // 백엔드에서는 기본 필터링만 수행 (하위 호환성을 위해 파라미터는 전달)
    if (annc_type && annc_type !== '전체' && annc_type !== '') {
        queryParams.append('annc_type', annc_type);
    }
    
    // agency 파라미터 추가 (전체가 아닌 경우만)
    if (agency && agency !== '전체' && agency !== '') {
        queryParams.append('agency', agency);
    }
    
    const response = await fetch(`/api/anncs?${queryParams}`);
    
    if (!response.ok) {
        throw new Error(`API 호출 실패: ${response.status}`);
    }
    
    const data = await response.json();
    return data.data || {};
}

/**
 * 공고 요약 정보 조회
 * 
 * @returns {Promise<Object>} 공고 요약 데이터
 */
async function getAnnouncementSummary() {
    const response = await fetch('/api/annc_summary');
    
    if (!response.ok) {
        throw new Error(`API 호출 실패: ${response.status}`);
    }
    
    const data = await response.json();
    return data.data || {};
}