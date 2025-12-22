/**
 * ZIPFIT - 메인 JavaScript
 * 공통 기능 및 인터랙션
 *
 * 참고: api.js에서 getOrCreateUserKey, getCurrentSessionId, createSessionId 함수 제공
 * main.js는 api.js를 먼저 로드한 후 사용해야 합니다.
 */

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', function() {
  try {
    initMobileMenu();
    initNavigationHighlight();
    initChatFeatures();
    initSearchFilters();
  } catch (err) {
    console.error('[main.js 초기화 오류]', err);
  }
});

/**
 * 모바일 메뉴 토글
 */
function initMobileMenu() {
  const menuToggle = document.querySelector('.mobile-menu-toggle');
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.querySelector('.sidebar-overlay');
  
  if (menuToggle && sidebar) {
    menuToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      sidebar.classList.toggle('show');
      sidebar.classList.toggle('active'); // active 클래스도 추가
      if (overlay) {
        overlay.classList.toggle('show');
        overlay.classList.toggle('active'); // active 클래스도 추가
      }
    });
    
    if (overlay) {
      overlay.addEventListener('click', (e) => {
        e.stopPropagation();
        sidebar.classList.remove('show');
        sidebar.classList.remove('active');
        overlay.classList.remove('show');
        overlay.classList.remove('active');
      });
    }
  }
}

// 전역 toggleSidebar 함수 (템플릿에서 사용)
window.toggleSidebar = function() {
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.querySelector('.sidebar-overlay');
  
  if (sidebar) {
    sidebar.classList.toggle('show');
    sidebar.classList.toggle('active');
    if (overlay) {
      overlay.classList.toggle('show');
      overlay.classList.toggle('active');
    }
  }
};

/**
 * 네비게이션 활성화 표시
 */
function initNavigationHighlight() {
  const currentPath = window.location.pathname;
  const navItems = document.querySelectorAll('.nav-item');
  
  navItems.forEach(item => {
    const href = item.getAttribute('href');
    if (href && currentPath.includes(href)) {
      item.classList.add('active');
    }
  });
}

/**
 * 채팅 기능
 */
function initChatFeatures() {
  // 추천 질문 클릭
  const questionBtns = document.querySelectorAll('.question-btn');
  const chatInput = document.querySelector('.chat-input');
  
  if (questionBtns.length && chatInput) {
    questionBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        chatInput.value = btn.textContent.trim();
        chatInput.focus();
      });
    });
  }
  
  // 메시지 전송
  const sendBtn = document.querySelector('.chat-send-btn');
  if (sendBtn && chatInput) {
    sendBtn.addEventListener('click', () => {
      sendMessage();
    });
    
    chatInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        sendMessage();
      }
    });
  }
}

/**
 * 메시지 전송 함수
 */
function sendMessage() {
  const chatInput = document.querySelector('.chat-input');
  if (chatInput && chatInput.value.trim()) {
    // 여기에 실제 메시지 전송 로직 추가
    console.log('메시지 전송:', chatInput.value);
    
    // Django AJAX 요청 예시
    // fetch('/api/chat/', {
    //   method: 'POST',
    //   headers: {
    //     'Content-Type': 'application/json',
    //     'X-CSRFToken': getCookie('csrftoken')
    //   },
    //   body: JSON.stringify({ message: chatInput.value })
    // })
    // .then(response => response.json())
    // .then(data => {
    //   console.log('응답:', data);
    //   addMessage(data);
    // });
    
    chatInput.value = '';
  }
}

/**
 * 검색 및 필터 기능
 */
function initSearchFilters() {
  // 검색
  const searchInput = document.querySelector('.search-box input');
  if (searchInput) {
    searchInput.addEventListener('input', debounce((e) => {
      const query = e.target.value.trim();
      console.log('검색:', query);
      
      // Django AJAX 요청 예시
      // fetch(`/api/search/?q=${encodeURIComponent(query)}`)
      //   .then(response => response.json())
      //   .then(data => updateSearchResults(data));
    }, 300));
  }
  
  // 필터
  const filterSelects = document.querySelectorAll('.filter-select');
  filterSelects.forEach(select => {
    select.addEventListener('change', (e) => {
      console.log('필터:', e.target.value);
      
      // Django AJAX 요청 예시
      // const filters = getActiveFilters();
      // fetch('/api/announcements/?' + new URLSearchParams(filters))
      //   .then(response => response.json())
      //   .then(data => updateAnnouncementList(data));
    });
  });
}

/**
 * 디바운스 유틸리티
 */
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

/**
 * Django CSRF 토큰 가져오기
 */
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

/**
 * 로딩 표시
 */
function showLoading() {
  // 로딩 스피너 표시
  const loader = document.createElement('div');
  loader.className = 'loading-spinner';
  loader.innerHTML = '<div class="spinner"></div>';
  document.body.appendChild(loader);
}

function hideLoading() {
  const loader = document.querySelector('.loading-spinner');
  if (loader) {
    loader.remove();
  }
}

/**
 * 알림 토스트
 */
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.classList.add('show');
  }, 100);
  
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

/**
 * 페이지 네비게이션
 */
function navigateTo(url) {
  window.location.href = url;
}

/**
 * AI 상담 버튼 클릭
 */
document.addEventListener('click', function(e) {
  if (e.target.classList.contains('btn-ai')) {
    navigateTo('chat.html');
  }
  
  if (e.target.classList.contains('btn-detail')) {
    // 공고 상세 페이지로 이동
    console.log('공고 상세 페이지로 이동');
    // navigateTo(`detail.html?id=${announcementId}`);
  }
});

/**
 * 폼 검증
 */
function validateForm(formElement) {
  const inputs = formElement.querySelectorAll('input[required], textarea[required], select[required]');
  let isValid = true;
  
  inputs.forEach(input => {
    if (!input.value.trim()) {
      isValid = false;
      input.classList.add('error');
      showError(input, '필수 항목입니다.');
    } else {
      input.classList.remove('error');
      clearError(input);
    }
  });
  
  return isValid;
}

function showError(input, message) {
  let errorDiv = input.nextElementSibling;
  if (!errorDiv || !errorDiv.classList.contains('error-message')) {
    errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    input.parentNode.insertBefore(errorDiv, input.nextSibling);
  }
  errorDiv.textContent = message;
}

function clearError(input) {
  const errorDiv = input.nextElementSibling;
  if (errorDiv && errorDiv.classList.contains('error-message')) {
    errorDiv.remove();
  }
}

// Export functions for Django integration
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    getCookie,
    showToast,
    showLoading,
    hideLoading,
    validateForm,
    navigateTo
  };
}
