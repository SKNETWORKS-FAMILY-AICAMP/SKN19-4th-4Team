/**
 * Mock 데이터
 * 실제 API 응답 형식에 맞춰 작성된 Mock 데이터
 * 
 * 사용법:
 * - 개발 중에는 이 Mock 데이터 사용
 * - 실제 API 연동 시에는 api.js의 실제 API 호출 함수 사용
 */

// ============================================
// 개발 모드 설정
// ============================================
// const USE_MOCK_DATA = true;  // Mock 데이터 사용
const USE_MOCK_DATA = false;  // 실제 API 사용

// ============================================
// 1. GET /api/annc_summary Mock 데이터
// ============================================
const mockAnncSummary = {
    "message": "성공적으로 공고 요약 정보를 조회했습니다.",
    "status": "success",
    "data": {
        "cnt_total": 1247,
        "cnt_lease": 800,
        "cnt_sale": 400,
        "cnt_etc": 47
    }
};

// 추가 통계 데이터 (main.html의 다른 통계용)
// 전역 변수로 사용 가능하도록 window 객체에 할당
window.mockStats = {
    "new_this_week": 42,
    "total_chat": 15823,
    "active_users": 3492
};
const mockStats = window.mockStats; // 하위 호환성

// ============================================
// 2. GET /api/anncs Mock 데이터
// ============================================
// 오늘 날짜 기준으로 다양한 모집기간을 가진 공고 생성
function generateMockAnnouncements() {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const announcements = [];
    
    // 다양한 기관, 유형, 상태 조합
    const agencies = ['LH', 'SH', 'GH'];
    const types = [
        { keyword: '영구임대주택', name: '영구임대주택' },
        { keyword: '행복주택', name: '행복주택' },
        { keyword: '분양주택', name: '분양주택' },
        { keyword: '전세임대주택', name: '전세임대주택' },
        { keyword: '매입임대주택', name: '매입임대주택' },
        { keyword: '국민임대주택', name: '국민임대주택' },
        { keyword: '통합공공임대주택', name: '통합공공임대주택' }
    ];
    
    // 지역 설정: LH는 전체, SH는 서울만, GH는 경기만
    const seoulRegions = ['서울', '강남', '강북', '송파', '강동', '서초', '마포', '용산', '종로', '중구'];
    const gyeonggiRegions = ['경기', '수원', '성남', '고양', '부천', '세종', '안양', '안산', '평택', '의정부', '시흥', '김포', '광명', '광주', '군포', '이천'];
    const allRegions = ['서울', '경기', '인천', '부산', '대전', '광주', '울산', '세종', '강원', '충청', '전라', '경상'];
    
    let id = 1;
    
    // 각 기관별로 다양한 공고 생성
    agencies.forEach((agency, agencyIdx) => {
        types.forEach((type, typeIdx) => {
            // 상태별로 다양한 날짜 생성
            const statusVariations = [
                { status: '공고중', daysAgo: 5, duration: 15 },   // 현재 진행 중
                { status: '접수중', daysAgo: 2, duration: 10 },   // 접수 중
                { status: '마감', daysAgo: 30, duration: 20 },    // 과거 마감
                { status: '공고예정', daysAgo: -5, duration: 25 } // 미래 공고
            ];
            
            statusVariations.forEach((statusVar, statusIdx) => {
                // 기관별 지역 선택
                let region = '';
                let regionList = [];
                if (agency === 'LH') {
                    regionList = allRegions;
                } else if (agency === 'SH') {
                    regionList = seoulRegions;
                } else if (agency === 'GH') {
                    regionList = gyeonggiRegions;
                }
                
                const regionIdx = (agencyIdx * types.length * statusVariations.length + typeIdx * statusVariations.length + statusIdx) % regionList.length;
                region = regionList[regionIdx];
                
                // 날짜 계산 (2024년-현재, 2025년 12월 11일 기준 다양하게)
                const createdDate = new Date(today);
                createdDate.setDate(createdDate.getDate() - statusVar.daysAgo);
                
                // 모집 시작일과 종료일 계산
                const startDate = new Date(createdDate);
                startDate.setDate(startDate.getDate() + 1);
                
                const endDate = new Date(startDate);
                endDate.setDate(endDate.getDate() + statusVar.duration);
                
                // 현재 날짜 기준으로 실제 상태 계산
                let actualStatus = statusVar.status;
                if (endDate < today) {
                    actualStatus = '마감';
                } else if (startDate > today) {
                    actualStatus = '공고예정';
                } else if (actualStatus === '접수중') {
                    actualStatus = '접수중';
                } else {
                    actualStatus = '공고중';
                }
                
                // 기관별 URL 설정 (mockData는 실제 공고가 아니므로 각 기관 사이트 링크)
                let url = '';
                if (agency === 'LH') {
                    url = 'https://apply.lh.or.kr/lhapply/main.do';
                } else if (agency === 'SH') {
                    url = 'https://www.i-sh.co.kr/main/index.do';
                } else if (agency === 'GH') {
                    url = 'https://www.gh.or.kr/';
                }
                
                announcements.push({
                    "annc_id": id++,
                    "annc_title": `${region} ${type.name} 입주자 모집공고`,
                    "annc_url": url,
                    "created_at": createdDate.toISOString(),
                    "annc_status": actualStatus,
                    // 프론트엔드에서 사용할 수 있도록 모집 기간 정보 추가 (선택적)
                    "recruitment_start_date": startDate.toISOString().split('T')[0],
                    "recruitment_end_date": endDate.toISOString().split('T')[0]
                });
            });
        });
    });
    
    return announcements;
}

const mockAnncList = {
    "message": "성공적으로 공고 목록을 조회했습니다.",
    "status": "success",
    "data": {
        "page_info": {
            "total_count": 84, // 3개 기관 * 7개 유형 * 4개 상태 = 84개
            "current_page": 1,
            "items_per_page": 10,
            "total_pages": 9
        },
        "items": generateMockAnnouncements()
    }
};

// ============================================
// 3. GET /api/chathistories Mock 데이터
// ============================================
const mockChatHistories = {
    "message": "성공적으로 채팅 히스토리 목록을 조회했습니다.",
    "status": "success",
    "data": [
        {
            "title": "수원 신혼부부 추천 분양",
            "session_id": "session-001"
        },
        {
            "title": "공고 비교 문의",
            "session_id": "session-002"
        },
        {
            "title": "청년 주택 공고 문의",
            "session_id": "session-003"
        }
    ]
};

// ============================================
// 4. GET /api/chathistories/{session_id} Mock 데이터
// ============================================
// 다양한 채팅 히스토리 시나리오
const mockChatHistoryScenarios = {
    "session-001": {
        "title": "수원 신혼부부 추천 분양",
        "session_id": "session-001",
        "user_key": "101",
        "chat_list": [
            {
                "id": 1,
                "sequence": 1,
                "message_type": "user",
                "message": "수원 지역 신혼부부 주택 추천해줘"
            },
            {
                "id": 2,
                "sequence": 2,
                "message_type": "bot",
                "message": "수원 지역 신혼부부 주택 공고를 찾았습니다.\n\n**추천 공고:**\n1. **수원 행복주택 입주자 모집공고**\n   - 위치: 경기도 수원시 영통구\n   - 공급호수: 120호\n   - 모집기간: 2025.12.01 ~ 2025.12.20\n   - 자격요건: 혼인기간 7년 이내 무주택 세대주\n\n2. **수원 분양주택 입주자 모집공고**\n   - 위치: 경기도 수원시 팔달구\n   - 공급호수: 85호\n   - 모집기간: 2025.12.05 ~ 2025.12.25\n\n더 자세한 정보를 원하시면 특정 공고를 선택해주세요."
            },
            {
                "id": 3,
                "sequence": 3,
                "message_type": "user",
                "message": "행복주택 자격 조건 알려줘"
            },
            {
                "id": 4,
                "sequence": 4,
                "message_type": "bot",
                "message": "행복주택 신혼부부 자격 조건은 다음과 같습니다:\n\n**✓ 기본 요건**\n- 혼인기간 7년 이내인 무주택 세대주\n- 해당 지역 거주 요건 충족\n\n**✓ 소득 기준**\n- 도시근로자 월평균 소득의 140% 이하\n- 맞벌이의 경우 160% 이하\n\n**✓ 자산 기준**\n- 총자산: 3억 6,100만원 이하\n- 자동차: 3,683만원 이하\n\n현재 귀하의 정보로 자격 여부를 확인해드릴까요?"
            }
        ]
    },
    "session-002": {
        "title": "공고 비교 문의",
        "session_id": "session-002",
        "user_key": "101",
        "chat_list": [
            {
                "id": 1,
                "sequence": 1,
                "message_type": "user",
                "message": "영구임대주택과 행복주택 차이점 알려줘"
            },
            {
                "id": 2,
                "sequence": 2,
                "message_type": "bot",
                "message": "영구임대주택과 행복주택의 주요 차이점을 비교해드리겠습니다:\n\n**영구임대주택**\n- 임대기간: 영구 임대\n- 대상: 무주택 서민층\n- 소득기준: 도시근로자 월평균 소득의 50% 이하\n- 임대료: 시세의 30~50% 수준\n\n**행복주택**\n- 임대기간: 20년 임대 (일부 30년)\n- 대상: 청년, 신혼부부, 노인 등\n- 소득기준: 도시근로자 월평균 소득의 100~120% 이하\n- 임대료: 시세의 60~80% 수준\n\n**주요 차이점**\n1. 임대기간: 영구임대는 평생, 행복주택은 20~30년\n2. 소득기준: 영구임대가 더 낮음\n3. 임대료: 영구임대가 더 저렴\n\n어떤 유형이 더 적합한지 확인해드릴까요?"
            },
            {
                "id": 3,
                "sequence": 3,
                "message_type": "user",
                "message": "현재 모집 중인 영구임대주택 공고 알려줘"
            },
            {
                "id": 4,
                "sequence": 4,
                "message_type": "bot",
                "message": "현재 모집 중인 영구임대주택 공고입니다:\n\n**1. 서울 영구임대주택 입주자 모집공고**\n   - 위치: 서울시 강남구\n   - 공급호수: 200호\n   - 모집기간: 2025.12.01 ~ 2025.12.20\n   - D-day: D-9\n\n**2. 경기 영구임대주택 입주자 모집공고**\n   - 위치: 경기도 성남시 분당구\n   - 공급호수: 150호\n   - 모집기간: 2025.12.05 ~ 2025.12.25\n   - D-day: D-14\n\n**3. 인천 영구임대주택 입주자 모집공고**\n   - 위치: 인천시 남동구\n   - 공급호수: 180호\n   - 모집기간: 2025.12.10 ~ 2025.12.30\n   - D-day: D-19\n\n더 자세한 정보는 '공고 목록' 메뉴에서 확인하실 수 있습니다."
            }
        ]
    },
    "session-003": {
        "title": "청년 주택 공고 문의",
        "session_id": "session-003",
        "user_key": "101",
        "chat_list": [
            {
                "id": 1,
                "sequence": 1,
                "message_type": "user",
                "message": "청년 주택 공고 알려줘"
            },
            {
                "id": 2,
                "sequence": 2,
                "message_type": "bot",
                "message": "현재 모집 중인 청년 주택 공고는 다음과 같습니다:\n\n**1. LH 고양삼송 청년 행복주택**\n   • 접수기간: 2025.12.01 ~ 12.20\n   • 위치: 경기도 고양시 덕양구\n   • 공급호수: 248호\n   • D-day: D-9\n\n**2. SH 강남 청년 매입임대주택**\n   • 접수기간: 2025.12.05 ~ 12.25\n   • 위치: 서울시 강남구\n   • 공급호수: 120호\n   • D-day: D-14\n\n**3. GH 판교 청년 전세임대**\n   • 접수기간: 2025.12.10 ~ 12.30\n   • 위치: 경기도 성남시 분당구\n   • 공급호수: 85호\n   • D-day: D-19\n\n더 자세한 정보를 원하시면 공고 목록 메뉴에서 확인하실 수 있습니다."
            },
            {
                "id": 3,
                "sequence": 3,
                "message_type": "user",
                "message": "청년 주택 자격 조건은?"
            },
            {
                "id": 4,
                "sequence": 4,
                "message_type": "bot",
                "message": "청년 주택 자격 조건은 다음과 같습니다:\n\n**✓ 기본 요건**\n- 만 19세 이상 ~ 만 39세 이하 (공고 접수일 기준)\n- 무주택자\n- 해당 지역 거주 또는 거주 예정자\n\n**✓ 소득 기준**\n- 도시근로자 월평균 소득의 100% 이하\n- 단독 세대주 또는 배우자와 함께 거주하는 세대주\n\n**✓ 자산 기준**\n- 총자산: 2억 4,000만원 이하\n- 자동차: 2,600만원 이하\n\n**✓ 청약통장**\n- 청약통장 가입기간 1년 이상\n- 납입횟수 12회 이상\n\n현재 귀하의 정보로 자격 여부를 확인해드릴까요?"
            }
        ]
    }
};

// 기본 mockChatHistoryDetail (하위 호환성)
const mockChatHistoryDetail = {
    "message": "성공적으로 특정 채팅 히스토리를 조회했습니다.",
    "status": "success",
    "data": mockChatHistoryScenarios["session-001"]
};

// ============================================
// 5. POST /api/chat Mock 데이터
// ============================================
const mockChatResponse = {
    "message": "성공적으로 메시지를 등록하고 AI 응답을 받았습니다.",
    "status": "success",
    "data": {
        "ai_response": {
            "id": 101,
            "session_id": "8a7e0d3c-9b1f-4d2a-8c5e-6f4b3a2d1e0f",
            "sequence": 2,
            "message_type": "bot",
            "message": "AI가 답변합니다: 'string'에 대한 정보입니다."
        }
    }
};

// ============================================
// Mock API 함수 (개발용)
// ============================================

/**
 * Mock API 호출 함수
 * 실제 API와 동일한 인터페이스를 제공하지만 Mock 데이터 반환
 */
const MockAPI = {
    /**
     * 공고 요약 정보 조회 (Mock)
     */
    async getAnnouncementSummary() {
        // 시뮬레이션: API 호출 지연
        await new Promise(resolve => setTimeout(resolve, 300));
        // 이번 주 신규 공고 수 추가 (mock 데이터)
        return {
            ...mockAnncSummary,
            data: {
                ...mockAnncSummary.data,
                cnt_new_this_week: window.mockStats?.new_this_week || 42
            }
        };
    },

    /**
     * 공고 목록 조회 (Mock)
     */
    async getAnnouncements(params = {}) {
        await new Promise(resolve => setTimeout(resolve, 300));
        
        // 파라미터에 따라 필터링
        let items = [...mockAnncList.data.items];
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        // 상태 필터링 (오늘 날짜 기준으로 재계산)
        if (params.annc_status && params.annc_status !== '' && params.annc_status !== '전체') {
            items = items.filter(item => {
                const createdDate = item.created_at ? new Date(item.created_at) : today;
                const startDate = new Date(createdDate);
                startDate.setDate(startDate.getDate() + 1);
                const endDate = new Date(startDate);
                if (item.annc_status === '마감') {
                    endDate.setDate(endDate.getDate() + 5);
                } else if (item.annc_status === '공고예정') {
                    endDate.setDate(endDate.getDate() + 20);
                } else {
                    endDate.setDate(endDate.getDate() + 14);
                }
                endDate.setHours(0, 0, 0, 0);
                
                const diffTime = endDate - today;
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                
                let calculatedStatus = item.annc_status;
                if (diffDays < 0) {
                    calculatedStatus = '마감';
                } else if (startDate > today) {
                    calculatedStatus = '공고예정';
                } else if (item.annc_status === '접수중') {
                    calculatedStatus = '접수중';
                } else if (item.annc_status === '마감') {
                    calculatedStatus = '마감';
                } else if (item.annc_status === '공고예정') {
                    calculatedStatus = '공고예정';
                } else {
                    calculatedStatus = '공고중';
                }
                
                return calculatedStatus === params.annc_status;
            });
        }
        
        // 유형 필터링 (제목에서 추출)
        if (params.annc_type && params.annc_type !== '' && params.annc_type !== '전체') {
            items = items.filter(item => {
                const title = item.annc_title || '';
                let anncType = '';
                if (title.includes('영구임대')) anncType = '영구임대주택';
                else if (title.includes('행복주택')) anncType = '행복주택';
                else if (title.includes('분양주택') || title.includes('분양')) anncType = '분양주택';
                else if (title.includes('전세임대')) anncType = '전세임대주택';
                else if (title.includes('매입임대')) anncType = '매입임대주택';
                else if (title.includes('국민임대')) anncType = '국민임대주택';
                else if (title.includes('통합공공임대')) anncType = '통합공공임대주택';
                
                return anncType === params.annc_type;
            });
        }
        
        // 기관 필터링 (URL에서 추출 또는 제목에서 추출)
        if (params.agency && params.agency !== '' && params.agency !== '전체') {
            items = items.filter(item => {
                let agency = 'LH';
                const title = item.annc_title || '';
                
                // URL에서 기관 추출
                if (item.annc_url) {
                    if (item.annc_url.includes('i-sh.co.kr')) agency = 'SH';
                    else if (item.annc_url.includes('gh.or.kr') || item.annc_url.includes('www.gh.or.kr')) agency = 'GH';
                    else if (item.annc_url.includes('lh.or.kr') || item.annc_url.includes('apply.lh.or.kr')) agency = 'LH';
                }
                
                // 제목에서 기관 추출 (백업)
                if (agency === 'LH') {
                    if (title.includes('서울') && !title.includes('경기')) agency = 'SH';
                    else if (title.includes('경기') || title.includes('수원') || title.includes('성남') || title.includes('고양') || title.includes('부천') || title.includes('세종')) agency = 'GH';
                }
                
                return agency === params.agency;
            });
        }
        
        // 제목 검색
        if (params.annc_title && params.annc_title !== '') {
            items = items.filter(item => 
                item.annc_title.toLowerCase().includes(params.annc_title.toLowerCase())
            );
        }
        
        // 페이지네이션 전에 전체 정렬 적용
        // 상태 우선순위 (공고중 > 접수중 > 공고예정 > 마감), 그 다음 날짜순 (최신순)
        const statusPriority = {
            '공고중': 1,
            '접수중': 2,
            '공고예정': 3,
            '마감': 4,
            '접수마감': 4
        };
        
        items.sort((a, b) => {
            // 상태 계산 함수
            const getStatus = (item) => {
                // 실제 API 데이터: annc_status가 명확하게 있는 경우
                if (item.annc_status && ['공고중', '접수중', '공고예정', '마감', '접수마감'].includes(item.annc_status)) {
                    return item.annc_status === '접수마감' ? '마감' : item.annc_status;
                }
                
                // mockData의 경우: 날짜 기반으로 상태 재계산
                const createdDate = item.created_at ? new Date(item.created_at) : today;
                const startDate = new Date(createdDate);
                
                if (item.annc_status === '공고예정') {
                    startDate.setDate(today.getDate() + Math.max(1, 3 + (item.annc_id % 7)));
                } else {
                    startDate.setDate(createdDate.getDate() + 1);
                    if (startDate < today) {
                        startDate.setTime(today.getTime());
                    }
                }
                
                const endDate = new Date(startDate);
                if (item.annc_status === '마감') {
                    endDate.setDate(startDate.getDate() - Math.max(1, item.annc_id % 5));
                } else if (item.annc_status === '공고예정') {
                    endDate.setDate(startDate.getDate() + 20 + (item.annc_id % 10));
                } else {
                    endDate.setDate(startDate.getDate() + 10 + (item.annc_id % 10));
                }
                endDate.setHours(0, 0, 0, 0);
                
                const diffTime = endDate - today;
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                
                if (diffDays < 0) return '마감';
                else if (startDate > today) return '공고예정';
                else if (item.annc_status === '접수중') return '접수중';
                else if (item.annc_status === '마감') return '마감';
                else if (item.annc_status === '공고예정') return '공고예정';
                else return '공고중';
            };
            
            const statusA = getStatus(a);
            const statusB = getStatus(b);
            
            const priorityA = statusPriority[statusA] || 5;
            const priorityB = statusPriority[statusB] || 5;
            
            // 상태가 다르면 상태 우선순위로 정렬
            if (priorityA !== priorityB) {
                return priorityA - priorityB;
            }
            
            // 상태가 같으면 날짜순 (최신순)
            const dateA = a.created_at ? new Date(a.created_at) : new Date(0);
            const dateB = b.created_at ? new Date(b.created_at) : new Date(0);
            return dateB - dateA; // 최신순
        });
        
        // 페이지네이션
        const page = params.current_page || 1;
        const perPage = params.items_per_page || 10;
        const start = (page - 1) * perPage;
        const end = start + perPage;
        const paginatedItems = items.slice(start, end);
        
        return {
            ...mockAnncList,
            data: {
                page_info: {
                    total_count: items.length,
                    current_page: page,
                    items_per_page: perPage,
                    total_pages: Math.ceil(items.length / perPage)
                },
                items: paginatedItems
            }
        };
    },

    /**
     * 채팅 히스토리 목록 조회 (Mock)
     */
    async getChatHistories(userKey) {
        await new Promise(resolve => setTimeout(resolve, 300));
        return mockChatHistories;
    },

    /**
     * 특정 채팅 히스토리 상세 조회 (Mock)
     */
    async getChatHistoryDetail(sessionId, userKey) {
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // 시나리오별로 다른 채팅 히스토리 반환
        if (typeof mockChatHistoryScenarios !== 'undefined' && mockChatHistoryScenarios[sessionId]) {
            return {
                "message": "성공적으로 특정 채팅 히스토리를 조회했습니다.",
                "status": "success",
                "data": mockChatHistoryScenarios[sessionId]
            };
        }
        
        // 기본 시나리오 반환 (session-001)
        const defaultScenario = mockChatHistoryScenarios && mockChatHistoryScenarios["session-001"] 
            ? mockChatHistoryScenarios["session-001"]
            : {
                "title": "수원 신혼부부 추천 분양",
                "session_id": "session-001",
                "user_key": userKey || "101",
                "chat_list": [
                    {
                        "id": 1,
                        "sequence": 1,
                        "message_type": "user",
                        "message": "추천해줘"
                    },
                    {
                        "id": 2,
                        "sequence": 2,
                        "message_type": "bot",
                        "message": "여기 추천 목록입니다."
                    }
                ]
            };
        
        return {
            "message": "성공적으로 특정 채팅 히스토리를 조회했습니다.",
            "status": "success",
            "data": defaultScenario
        };
    },

    /**
     * 채팅 메시지 전송 (Mock)
     */
    async sendChatMessage(userMessage, userKey, sessionId) {
        await new Promise(resolve => setTimeout(resolve, 800));
        
        // 질문에 따른 실제적인 Mock 응답 생성
        const responses = {
            '청년 주택 공고를 알려줘': '현재 모집 중인 청년 주택 공고는 다음과 같습니다:\n\n**1. LH 고양삼송 청년 행복주택**\n   • 접수기간: 2025.01.20 ~ 01.31\n   • 위치: 경기도 고양시 덕양구\n   • 공급호수: 248호\n\n**2. SH 강남 청년 매입임대주택**\n   • 접수기간: 2025.01.25 ~ 02.05\n   • 위치: 서울시 강남구\n   • 공급호수: 120호\n\n**3. GH 판교 청년 전세임대**\n   • 접수기간: 2025.02.01 ~ 02.15\n   • 위치: 경기도 성남시 분당구\n   • 공급호수: 85호\n\n더 자세한 정보를 원하시면 "공고 목록" 메뉴에서 확인하실 수 있습니다.',
            
            '신혼부부 특별공급 자격 조건은?': '신혼부부 특별공급 자격 조건은 다음과 같습니다:\n\n**✓ 기본 요건**\n1. 혼인기간 7년 이내인 무주택 세대주\n2. 해당 지역 거주 요건 충족\n\n**✓ 소득 기준**\n• 도시근로자 월평균 소득의 140% 이하\n• 맞벌이의 경우 160% 이하\n\n**✓ 자산 기준**\n• 총자산: 3억 6,100만원 이하\n• 자동차: 3,683만원 이하\n\n현재 귀하의 정보로 자격 여부를 확인해드릴까요?',
            
            'LH 청약 신청 방법 알려줘': 'LH 청약 신청 방법은 다음과 같습니다:\n\n**1단계: 준비**\n• LH 청약센터 홈페이지 접속 (apply.lh.or.kr)\n• 회원가입 및 로그인\n• 공인인증서 또는 간편인증 준비\n\n**2단계: 신청**\n• 원하는 주택 선택\n• 신청자격 확인 및 서류 제출\n• 청약 신청서 작성 및 제출\n\n**3단계: 확인**\n• 청약통장 가입기간 확인\n• 납입횟수 확인\n• 당첨자 발표 대기\n\n청약통장 가입기간과 납입횟수가 중요하니 미리 확인하세요!',
            
            '소득 3분위에 해당하는 주택은?': '소득 3분위(중위소득 50~70%)에 해당하는 주택은:\n\n**✓ 신청 가능한 주택 유형**\n\n1. **행복주택**\n   • 청년, 신혼부부 대상\n   • 시세 60~80% 수준\n\n2. **공공지원 민간임대주택**\n   • 시세 95% 수준\n   • 8년 임대 의무\n\n3. **통합공공임대주택**\n   • 30년 임대\n   • 시세 60~80% 수준\n\n귀하는 현재 3분위로 등록되어 있어 위 주택들의 신청 자격이 있습니다.\n구체적인 단지를 확인하시겠습니까?'
        };
        
        // 질문 매칭 (대소문자 무시, 부분 일치)
        let responseMessage = null;
        for (const [key, value] of Object.entries(responses)) {
            if (userMessage.includes(key) || key.includes(userMessage)) {
                responseMessage = value;
                break;
            }
        }
        
        // 매칭되지 않으면 기본 응답
        if (!responseMessage) {
            responseMessage = `"${userMessage}"에 대한 정보를 찾고 있습니다.\n\nLH, SH, GH의 공고 문서를 분석하여 정확한 답변을 제공해드리겠습니다.\n\n더 구체적인 질문을 해주시면 더 정확한 답변을 드릴 수 있습니다.\n예: "청년 주택 공고를 알려줘", "신혼부부 특별공급 자격 조건은?" 등`;
        }
        
        // Mock 응답 생성
        return {
            ...mockChatResponse,
            data: {
                ai_response: {
                    ...mockChatResponse.data.ai_response,
                    message: responseMessage,
                    sequence: Date.now() % 1000,
                    session_id: sessionId || 'mock-session-' + Date.now()
                }
            }
        };
    }
};

// ============================================
// 통합 API 함수 (Mock 또는 실제 API 자동 선택)
// ============================================
const API = {
    async getAnnouncementSummary() {
        if (USE_MOCK_DATA) {
            return await MockAPI.getAnnouncementSummary();
        } else {
            // 실제 API 호출: api.js의 getAnnouncementSummary는 { data: {...} } 형태 반환
            try {
                const response = await getAnnouncementSummary();
                // api.js의 getAnnouncementSummary는 data.data를 반환하므로, 표준 형식으로 래핑
                return {
                    status: 'success',
                    data: response || {}
                };
            } catch (error) {
                console.error('공고 요약 정보 조회 오류:', error);
                return {
                    status: 'error',
                    message: error.message || '공고 요약 정보를 불러오는 중 오류가 발생했습니다.',
                    data: {}
                };
            }
        }
    },

    async getAnnouncements(params) {
        if (USE_MOCK_DATA) {
            return await MockAPI.getAnnouncements(params);
        } else {
            // api.js의 getAnnouncements 함수 호출
            try {
                const response = await getAnnouncements(params);
                // api.js의 getAnnouncements는 data만 반환하므로 status와 함께 래핑
                return {
                    status: 'success',
                    data: response
                };
            } catch (error) {
                console.error('공고 목록 조회 오류:', error);
                return {
                    status: 'error',
                    message: error.message || '공고 목록을 불러오는 중 오류가 발생했습니다.',
                    data: {
                        page_info: {
                            total_count: 0,
                            current_page: params.current_page || 1,
                            items_per_page: params.items_per_page || 10,
                            total_pages: 0
                        },
                        items: []
                    }
                };
            }
        }
    },

    async getChatHistories(userKey) {
        if (USE_MOCK_DATA) {
            return await MockAPI.getChatHistories(userKey);
        } else {
            // 실제 API 호출: api.js의 getChatHistories는 배열을 반환
            try {
                const response = await getChatHistories(userKey);
                // api.js의 getChatHistories는 data.data 또는 배열을 반환하므로, 표준 형식으로 래핑
                return {
                    status: 'success',
                    data: response || []
                };
            } catch (error) {
                console.error('채팅 히스토리 목록 조회 오류:', error);
                return {
                    status: 'error',
                    message: error.message || '채팅 히스토리 목록을 불러오는 중 오류가 발생했습니다.',
                    data: []
                };
            }
        }
    },

    async getChatHistoryDetail(sessionId, userKey) {
        if (USE_MOCK_DATA) {
            return await MockAPI.getChatHistoryDetail(sessionId, userKey);
        } else {
            // 실제 API 호출: api.js의 getChatHistoryDetail은 { data: { chat_list: [...] } } 형태 반환
            try {
                const response = await getChatHistoryDetail(sessionId, userKey);
                // api.js의 getChatHistoryDetail은 data.data를 반환하므로, 이를 표준 형식으로 래핑
                // 실제 API 응답 구조: { data: { title, session_id, user_key, chat_list: [...] } }
                return {
                    status: 'success',
                    data: response || {}
                };
            } catch (error) {
                console.error('채팅 히스토리 상세 조회 오류:', error);
                return {
                    status: 'error',
                    message: error.message || '채팅 히스토리를 불러오는 중 오류가 발생했습니다.',
                    data: {}
                };
            }
        }
    },

    async sendChatMessage(userMessage, userKey, sessionId, userProfile = null, announcementId = null) {
        if (USE_MOCK_DATA) {
            return await MockAPI.sendChatMessage(userMessage, userKey, sessionId);
        } else {
            // 실제 API 호출: api.js의 sendChatMessage는 { data: { ai_response: {...} } } 형태 반환
            try {
                const response = await sendChatMessage(userMessage, userKey, sessionId, userProfile, announcementId);
                // api.js의 sendChatMessage는 이미 표준 형식으로 반환하므로 그대로 사용
                // 필요시 status 추가
                if (!response.status) {
                    return {
                        status: 'success',
                        ...response
                    };
                }
                return response;
            } catch (error) {
                console.error('채팅 메시지 전송 오류:', error);
                return {
                    status: 'error',
                    message: error.message || '메시지를 전송하는 중 오류가 발생했습니다.',
                    data: {}
                };
            }
        }
    }
};

// ============================================
// 통합 callApi 함수 (템플릿에서 사용)
// ============================================
/**
 * 통합 API 호출 함수
 * USE_MOCK_DATA 플래그에 따라 Mock 또는 실제 API 호출
 * 
 * @param {string} endpoint - API 엔드포인트 (예: '/api/anncs', '/api/chat')
 * @param {string} method - HTTP 메서드 ('GET', 'POST', 'PUT', 'DELETE')
 * @param {Object} body - 요청 본문 (POST/PUT 시 사용)
 * @returns {Promise<Object>} API 응답 데이터
 */
async function callApi(endpoint, method = 'GET', body = null) {
    if (USE_MOCK_DATA) {
        // Mock 데이터 사용
        console.log(`[MOCK API] ${method} ${endpoint}`, body);
        
        // 엔드포인트별 Mock 응답
        if (endpoint === '/api/annc_summary') {
            return await MockAPI.getAnnouncementSummary();
        } else if (endpoint.startsWith('/api/anncs')) {
            // 쿼리 파라미터 파싱
            let page = 1;
            let annc_status = '전체';
            let annc_type = '전체';
            let annc_title = '';
            
            try {
                const url = new URL(endpoint, window.location.origin);
                page = parseInt(url.searchParams.get('page') || url.searchParams.get('current_page') || '1');
                annc_status = url.searchParams.get('annc_status') || '전체';
                annc_type = url.searchParams.get('annc_type') || '전체';
                annc_title = url.searchParams.get('annc_title') || '';
            } catch (e) {
                // URL 파싱 실패 시 기본값 사용
                console.warn('URL 파싱 실패, 기본값 사용:', e);
            }
            
            return await MockAPI.getAnnouncements({
                current_page: page,
                annc_status,
                annc_type,
                annc_title
            });
        } else if (endpoint.startsWith('/api/chathistories/')) {
            // 특정 채팅 히스토리 상세 조회
            const sessionId = endpoint.split('/').pop().split('?')[0];
            const userKey = getOrCreateUserKey();
            return await MockAPI.getChatHistoryDetail(sessionId, userKey);
        } else if (endpoint.startsWith('/api/chathistories')) {
            // 채팅 히스토리 목록 조회
            const userKey = getOrCreateUserKey();
            const response = await MockAPI.getChatHistories(userKey);
            return {
                message: "성공적으로 채팅 히스토리 목록을 조회했습니다.",
                status: "success",
                data: response.data || response
            };
        } else if (endpoint === '/api/chat' && method === 'POST') {
            // 채팅 메시지 전송
            const userKey = getOrCreateUserKey();
            const sessionId = getOrCreateSessionId();
            const userMessage = body?.user_message || '';
            return await MockAPI.sendChatMessage(userMessage, userKey, sessionId);
        }
        
        // 기본 Mock 응답
        return {
            message: "Mock 응답",
            status: "success",
            data: {}
        };
    } else {
        // 실제 API 호출
        const userKey = getOrCreateUserKey();
        const sessionId = getOrCreateSessionId();
        
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        };
        
        if (body) {
            options.body = JSON.stringify({
                ...body,
                user_key: userKey,
                session_id: sessionId
            });
        } else if (method === 'POST' || method === 'PUT') {
            options.body = JSON.stringify({
                user_key: userKey,
                session_id: sessionId
            });
        }
        
        // 쿼리 파라미터에 user_key 추가 (GET 요청 시)
        if (method === 'GET' && !endpoint.includes('user_key=')) {
            const separator = endpoint.includes('?') ? '&' : '?';
            endpoint += `${separator}user_key=${encodeURIComponent(userKey)}`;
        }
        
        try {
            const response = await fetch(endpoint, options);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log(`[REAL API] Response from ${endpoint}:`, data);
            return data;
        } catch (error) {
            console.error(`[REAL API] Error calling ${endpoint}:`, error);
            throw error;
        }
    }
}

// session_id 관리 함수 (api.js와 호환)
function getOrCreateSessionId() {
    let sessionId = sessionStorage.getItem('current_session_id');
    if (!sessionId) {
        sessionId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
        sessionStorage.setItem('current_session_id', sessionId);
    }
    return sessionId;
}

