// 메인 페이지 JavaScript

// 설정 상수
const CONFIG = {
  // 날씨 API 설정 (예: OpenWeatherMap API 사용 시)
  WEATHER_API: {
    // TODO: 실제 날씨 API 키와 엔드포인트로 교체 필요
    // 예: 'https://api.openweathermap.org/data/2.5/weather?q=서울&appid=YOUR_API_KEY&units=metric&lang=kr'
    ENDPOINT: '',
    API_KEY: ''
  },
  // 게시판 설정
  POSTS: {
    RECRUIT_COUNT: 5,  // 모집 게시판 표시 개수
    NOTICE_COUNT: 5,   // 공지사항 표시 개수
    // TODO: 실제 API 엔드포인트로 교체 필요
    RECRUIT_API: '/api/recruit?sort=views&limit=5',
    NOTICE_API: '/api/notice?sort=latest&limit=5'
  },
  // 시설 설정
  FACILITIES: {
    COUNT: 3,  // 표시할 시설 개수
    // TODO: 실제 API 엔드포인트로 교체 필요
    API: '/api/facilities/random'
  }
};

// ============================================
// 5번 섹션: 오늘의 날씨
// ============================================
async function loadWeather() {
  const weatherInfo = document.getElementById('weatherInfo');
  
  try {
    // TODO: 실제 날씨 API 호출로 교체
    // 예시: OpenWeatherMap API 사용 시
    /*
    const response = await fetch(CONFIG.WEATHER_API.ENDPOINT);
    const data = await response.json();
    
    const temperature = data.main.temp;
    const description = data.weather[0].description;
    const precipitation = data.rain ? data.rain['1h'] || 0 : 0;
    const humidity = data.main.humidity;
    
    weatherInfo.innerHTML = `
      <div class="weather-temp">${Math.round(temperature)}°C</div>
      <div class="weather-desc">${description}</div>
      <div class="weather-detail">
        <div>강수량: ${precipitation}mm</div>
        <div>습도: ${humidity}%</div>
      </div>
    `;
    */
    
    // 임시 더미 데이터 (API 연동 전까지)
    weatherInfo.innerHTML = `
      <div class="weather-temp">15°C</div>
      <div class="weather-desc">맑음</div>
      <div class="weather-detail">
        <div>강수량: 0mm</div>
        <div>습도: 45%</div>
      </div>
    `;
    
  } catch (error) {
    console.error('날씨 정보 로드 실패:', error);
    weatherInfo.innerHTML = '<div class="weather-error">날씨 정보를 불러올 수 없습니다.</div>';
  }
}

// ============================================
// 5번 섹션: 모집 게시판 (조회순)
// ============================================
async function loadRecruitPosts() {
  const recruitList = document.getElementById('recruitList');
  
  try {
    // TODO: 실제 API 호출로 교체
    /*
    const response = await fetch(CONFIG.POSTS.RECRUIT_API);
    const posts = await response.json();
    
    if (posts.length === 0) {
      recruitList.innerHTML = '<li class="no-data">게시글이 없습니다.</li>';
      return;
    }
    
    recruitList.innerHTML = posts.map(post => `
      <li class="post-item" data-post-id="${post.id}">
        <a href="/recruit/${post.id}">${post.title}</a>
        <span class="post-views">조회: ${post.views}</span>
      </li>
    `).join('');
    
    // 클릭 이벤트 리스너 추가
    recruitList.querySelectorAll('.post-item').forEach(item => {
      item.addEventListener('click', () => {
        const postId = item.dataset.postId;
        window.location.href = `/recruit/${postId}`;
      });
    });
    */
    
    // 임시 더미 데이터 (API 연동 전까지)
    const dummyPosts = [
      { id: 1, title: '배드민턴 같이 하실 분 모집합니다.', views: 123 },
      { id: 2, title: '풋살 팀원 구합니다.', views: 89 },
      { id: 3, title: '농구 동호회 모집', views: 67 },
      { id: 4, title: '수영 강습 같이 받을 분', views: 45 },
      { id: 5, title: '테니스 파트너 구합니다.', views: 34 }
    ];
    
    if (dummyPosts.length === 0) {
      recruitList.innerHTML = '<li class="no-data">게시글이 없습니다.</li>';
      return;
    }
    
    recruitList.innerHTML = dummyPosts.map(post => `
      <li class="post-item" data-post-id="${post.id}">
        <a href="/recruit/${post.id}" class="post-link">${post.title}</a>
        <span class="post-views">조회: ${post.views}</span>
      </li>
    `).join('');
    
    // 클릭 이벤트 리스너 추가 (전체 아이템 클릭 가능하도록)
    recruitList.querySelectorAll('.post-item').forEach(item => {
      item.addEventListener('click', (e) => {
        // 링크 클릭 시에는 기본 동작 유지
        if (e.target.classList.contains('post-link')) return;
        
        const postId = item.dataset.postId;
        window.location.href = `/recruit/${postId}`;
      });
    });
    
  } catch (error) {
    console.error('모집 게시판 로드 실패:', error);
    recruitList.innerHTML = '<li class="error">게시글을 불러올 수 없습니다.</li>';
  }
}

// ============================================
// 5번 섹션: 공지사항 (최신순)
// ============================================
async function loadNotices() {
  const noticeList = document.getElementById('noticeList');
  
  try {
    // TODO: 실제 API 호출로 교체
    /*
    const response = await fetch(CONFIG.POSTS.NOTICE_API);
    const notices = await response.json();
    
    if (notices.length === 0) {
      noticeList.innerHTML = '<li class="no-data">공지사항이 없습니다.</li>';
      return;
    }
    
    noticeList.innerHTML = notices.map(notice => `
      <li class="notice-item" data-notice-id="${notice.id}">
        <a href="/notice/${notice.id}">${notice.title}</a>
        <span class="notice-date">${formatDate(notice.createdAt)}</span>
      </li>
    `).join('');
    
    // 클릭 이벤트 리스너 추가
    noticeList.querySelectorAll('.notice-item').forEach(item => {
      item.addEventListener('click', () => {
        const noticeId = item.dataset.noticeId;
        window.location.href = `/notice/${noticeId}`;
      });
    });
    */
    
    // 임시 더미 데이터 (API 연동 전까지)
    const dummyNotices = [
      { id: 1, title: '실내 체육관 정기 점검 안내', createdAt: '2024-01-15' },
      { id: 2, title: '수영장 운영 시간 변경 안내', createdAt: '2024-01-14' },
      { id: 3, title: '신규 시설 오픈 안내', createdAt: '2024-01-13' },
      { id: 4, title: '회원 혜택 안내', createdAt: '2024-01-12' },
      { id: 5, title: '시설 이용 규칙 변경 안내', createdAt: '2024-01-11' }
    ];
    
    if (dummyNotices.length === 0) {
      noticeList.innerHTML = '<li class="no-data">공지사항이 없습니다.</li>';
      return;
    }
    
    noticeList.innerHTML = dummyNotices.map(notice => `
      <li class="notice-item" data-notice-id="${notice.id}">
        <a href="/notice/${notice.id}" class="notice-link">${notice.title}</a>
        <span class="notice-date">${formatDate(notice.createdAt)}</span>
      </li>
    `).join('');
    
    // 클릭 이벤트 리스너 추가
    noticeList.querySelectorAll('.notice-item').forEach(item => {
      item.addEventListener('click', (e) => {
        // 링크 클릭 시에는 기본 동작 유지
        if (e.target.classList.contains('notice-link')) return;
        
        const noticeId = item.dataset.noticeId;
        window.location.href = `/notice/${noticeId}`;
      });
    });
    
  } catch (error) {
    console.error('공지사항 로드 실패:', error);
    noticeList.innerHTML = '<li class="error">공지사항을 불러올 수 없습니다.</li>';
  }
}

// 날짜 포맷팅 함수
function formatDate(dateString) {
  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// ============================================
// 6번 섹션: 시설 랜덤 표시
// ============================================
async function loadRandomFacilities() {
  const facilitiesSection = document.getElementById('facilitiesSection');
  
  try {
    // TODO: 실제 API 호출로 교체
    /*
    const response = await fetch(CONFIG.FACILITIES.API);
    const facilities = await response.json();
    
    // 랜덤으로 3개 선택 (서버에서 이미 랜덤 처리된 경우 그대로 사용)
    const selectedFacilities = facilities.slice(0, CONFIG.FACILITIES.COUNT);
    
    facilitiesSection.innerHTML = selectedFacilities.map(facility => `
      <article class="facility" data-facility-id="${facility.id}">
        <h3>${facility.name}</h3>
        <p>${facility.address}</p>
        <p>${facility.description}</p>
      </article>
    `).join('');
    */
    
    // 임시 더미 데이터 (API 연동 전까지)
    const dummyFacilities = [
      { id: 1, name: '시설 A', address: '서울시 강남구', description: '체육관' },
      { id: 2, name: '시설 B', address: '서울시 서초구', description: '수영장' },
      { id: 3, name: '시설 C', address: '서울시 송파구', description: '운동장' }
    ];
    
    facilitiesSection.innerHTML = dummyFacilities.map(facility => `
      <article class="facility" data-facility-id="${facility.id}">
        <h3>${facility.name}</h3>
        <p>${facility.address}</p>
        <p>${facility.description}</p>
      </article>
    `).join('');
    
  } catch (error) {
    console.error('시설 정보 로드 실패:', error);
    facilitiesSection.innerHTML = `
      <article class="facility error">시설 정보를 불러올 수 없습니다.</article>
      <article class="facility error">시설 정보를 불러올 수 없습니다.</article>
      <article class="facility error">시설 정보를 불러올 수 없습니다.</article>
    `;
  }
}


// ============================================
// 페이지 로드 시 초기화
// ============================================
document.addEventListener('DOMContentLoaded', () => {
  
  // 5번 섹션 데이터 로드
  loadWeather();
  loadRecruitPosts();
  loadNotices();
  
  // 6번 섹션 데이터 로드
  loadRandomFacilities();
});

