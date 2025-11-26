// ============================================
// 모바일 메뉴 토글
// ============================================
function initMobileMenu() {
  const menuBtn = document.getElementById('menuBtn');
  const gnb = document.getElementById('gnb');
  const overlay = document.getElementById('mobileMenuOverlay');
  const gnbItems = document.querySelectorAll('.gnb__item');

  if (!menuBtn || !gnb || !overlay) return;

  // 햄버거 메뉴 버튼 클릭
  menuBtn.addEventListener('click', () => {
    menuBtn.classList.toggle('active');
    gnb.classList.toggle('active');
    overlay.classList.toggle('active');
    document.body.style.overflow = gnb.classList.contains('active') ? 'hidden' : '';
  });

  // 오버레이 클릭 시 메뉴 닫기
  overlay.addEventListener('click', () => {
    menuBtn.classList.remove('active');
    gnb.classList.remove('active');
    overlay.classList.remove('active');
    document.body.style.overflow = '';
  });

  // 모바일 메뉴 아이템 클릭 (서브메뉴 토글)
  gnbItems.forEach(item => {
    const link = item.querySelector('.gnb__link');
    if (link) {
      link.addEventListener('click', (e) => {
        // 데스크탑에서는 기본 동작 유지
        if (window.innerWidth > 768) return;
        
        // 모바일에서는 서브메뉴 토글
        const submenu = item.querySelector('.gnb__submenu');
        if (submenu) {
          e.preventDefault();
          item.classList.toggle('active');
        }
      });
    }
  });

  // 화면 크기 변경 시 메뉴 닫기
  window.addEventListener('resize', () => {
    if (window.innerWidth > 768) {
      menuBtn.classList.remove('active');
      gnb.classList.remove('active');
      overlay.classList.remove('active');
      document.body.style.overflow = '';
    }
  });
}

$(document).ready(function(){
    initMobileMenu(); 
})