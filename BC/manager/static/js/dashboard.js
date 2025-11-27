document.addEventListener('DOMContentLoaded', function() {
    // 1. 예약/모집글 일별 추이
    const dailyTrendCtx = document.getElementById('dailyTrendChart');
    if (dailyTrendCtx) {
        const recruitment = dailyRecruitment || {};
        const reservations = dailyReservations || {};
        
        // 날짜 정렬
        const allDates = [...new Set([...Object.keys(recruitment), ...Object.keys(reservations)])].sort();
        
        const recruitmentData = allDates.map(date => recruitment[date] || 0);
        const reservationData = allDates.map(date => reservations[date] || 0);
        
        new Chart(dailyTrendCtx, {
            type: 'line',
            data: {
                labels: allDates,
                datasets: [{
                    label: '모집글',
                    data: recruitmentData,
                    borderColor: 'rgb(52, 152, 219)',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: '예약',
                    data: reservationData,
                    borderColor: 'rgb(46, 204, 113)',
                    backgroundColor: 'rgba(46, 204, 113, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // 2. 모집 완료 추이
    const completionCtx = document.getElementById('completionChart');
    if (completionCtx) {
        const trend = completionTrend || {};
        const labels = Object.keys(trend).sort();
        const totalData = labels.map(date => trend[date]?.total || 0);
        const completedData = labels.map(date => trend[date]?.completed || 0);
        
        new Chart(completionCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '전체',
                    data: totalData,
                    backgroundColor: 'rgba(149, 165, 166, 0.5)'
                }, {
                    label: '완료',
                    data: completedData,
                    backgroundColor: 'rgba(46, 204, 113, 0.7)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // 3. 회원 가입 추이
    const memberCtx = document.getElementById('memberChart');
    if (memberCtx) {
        const members = dailyMembers || {};
        const labels = Object.keys(members).sort();
        const memberData = labels.map(date => members[date] || 0);
        
        new Chart(memberCtx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '신규 회원',
                    data: memberData,
                    borderColor: 'rgb(155, 89, 182)',
                    backgroundColor: 'rgba(155, 89, 182, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // 4. 성별 분포
    const genderCtx = document.getElementById('genderChart');
    if (genderCtx) {
        const gender = genderData || {};
        const labels = [];
        const data = [];
        
        // gender 데이터가 '0', '1' 키로 되어있을 수 있음
        if (gender['0'] !== undefined || gender['1'] !== undefined) {
            labels.push('남성', '여성');
            data.push(gender['0'] || 0, gender['1'] || 0);
        } else {
            // 다른 형식일 경우
            const keys = Object.keys(gender);
            keys.forEach(key => {
                labels.push(key === '0' ? '남성' : key === '1' ? '여성' : key);
                data.push(gender[key]);
            });
        }
        
        new Chart(genderCtx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [
                        'rgba(52, 152, 219, 0.8)',
                        'rgba(231, 76, 60, 0.8)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom'
                    }
                }
            }
        });
    }

    // 5. 게시판 통계
    const boardCtx = document.getElementById('boardChart');
    if (boardCtx && boardStats && boardStats.length > 0) {
        const boardLabels = boardStats.map(b => b.board_id__board_name || '기타');
        const boardData = boardStats.map(b => b.count);
        
        new Chart(boardCtx, {
            type: 'bar',
            data: {
                labels: boardLabels,
                datasets: [{
                    label: '게시글 수',
                    data: boardData,
                    backgroundColor: 'rgba(241, 196, 15, 0.7)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    } else if (boardCtx) {
        // 데이터가 없을 때
        boardCtx.parentElement.innerHTML = '<p style="text-align: center; color: #7f8c8d; padding: 40px;">게시판 데이터가 없습니다.</p>';
    }

    // 6. 지역별 평균 평점
    const ratingCtx = document.getElementById('ratingChart');
    if (ratingCtx) {
        const ratings = regionRatings || {};
        const labels = Object.keys(ratings);
        const avgData = labels.map(region => {
            const rating = ratings[region];
            return rating && rating.mean ? rating.mean : 0;
        });
        
        if (labels.length > 0) {
            new Chart(ratingCtx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '평균 평점',
                        data: avgData,
                        backgroundColor: 'rgba(46, 204, 113, 0.7)'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 5
                        }
                    }
                }
            });
        } else {
            ratingCtx.parentElement.innerHTML = '<p style="text-align: center; color: #7f8c8d; padding: 40px;">평점 데이터가 없습니다.</p>';
        }
    }
});

