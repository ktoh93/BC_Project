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
// ============================================
// 랜덤 시설 표시 (템플릿 섹션)
// 서버에서 이미 데이터를 렌더링하므로 JavaScript는 사용하지 않음
// ============================================
async function loadRandomFacilities() {
  // 서버 사이드에서 이미 데이터를 렌더링하므로 이 함수는 더 이상 사용하지 않음
  // 필요시 클라이언트 사이드에서 추가 로딩이 필요할 때만 사용
  return;
}


// ============================================
// 페이지 로드 시 초기화
// ============================================
document.addEventListener('DOMContentLoaded', () => {
  loadWeather();
  // loadRandomFacilities(); // 서버 사이드에서 이미 렌더링하므로 주석 처리
});

