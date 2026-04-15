import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from utils.auth import is_logged_in, get_role
from utils.sidebar import render_sidebar

if not is_logged_in():
    st.switch_page("app.py")
if get_role() != "admin":
    st.switch_page("app.py")

render_sidebar()

# ── 데이터 ──
company_data = {
    "스카이렌터카": {"sessions": 5,  "events": 18, "avg_score": 68, "blacklist": 1},
    "제주렌터카":   {"sessions": 4,  "events": 21, "avg_score": 74, "blacklist": 2},
    "스타렌터카":   {"sessions": 3,  "events": 8,  "avg_score": 81, "blacklist": 0},
}

default_scoring = {
    "스카이렌터카": {"급출발 감점": 12, "급제동 감점": 10, "근접+급가속 감점": 8,  "근접+과속 감점": 6, "블랙리스트 기준점": 35, "Green 등급 최소점수": 75},
    "제주렌터카":   {"급출발 감점": 15, "급제동 감점": 15, "근접+급가속 감점": 12, "근접+과속 감점": 8, "블랙리스트 기준점": 25, "Green 등급 최소점수": 85},
    "스타렌터카":   {"급출발 감점": 10, "급제동 감점": 10, "근접+급가속 감점": 8,  "근접+과속 감점": 6, "블랙리스트 기준점": 30, "Green 등급 최소점수": 80},
}

perf_by_company = {
    "스카이렌터카": {"yolo_map": 0.92, "yolo_fps": 35.8, "depth_map": 0.88, "depth_fps": 1.0, "latency": "45ms", "packet_loss": "0.3%"},
    "제주렌터카":   {"yolo_map": 0.91, "yolo_fps": 34.2, "depth_map": 0.87, "depth_fps": 0.9, "latency": "52ms", "packet_loss": "0.5%"},
    "스타렌터카":   {"yolo_map": 0.93, "yolo_fps": 36.1, "depth_map": 0.89, "depth_fps": 1.1, "latency": "41ms", "packet_loss": "0.2%"},
}

system_logs = [
    {"시간": "2026-04-07 14:32:05", "유형": "시스템",   "설명": "YOLO 모델 추론 지연 경고 – 평균 42ms 초과"},
    {"시간": "2026-04-07 14:31:42", "유형": "네트워크", "설명": "패킷 손실률 1.2% 감지 – 임계값 초과"},
    {"시간": "2026-04-07 14:30:18", "유형": "시스템",   "설명": "Depth 모델 FPS 저하 – 0.7fps"},
    {"시간": "2026-04-07 14:29:55", "유형": "네트워크", "설명": "서버 응답 지연 – latency 85ms"},
    {"시간": "2026-04-07 14:28:30", "유형": "시스템",   "설명": "프레임 드롭 감지 – 5프레임 연속 누락"},
    {"시간": "2026-04-07 14:27:10", "유형": "시스템",   "설명": "GPU 메모리 사용량 92% – 위험 수준"},
    {"시간": "2026-04-07 14:25:45", "유형": "네트워크", "설명": "CAN 버스 통신 정상 복구"},
    {"시간": "2026-04-07 14:24:00", "유형": "시스템",   "설명": "모델 체크포인트 자동 저장 완료"},
]

bottleneck_data = pd.DataFrame({
    "추론 시간(ms)": np.random.uniform(10, 45, 50).round(1),
    "전송 지연(ms)": np.random.uniform(5, 30, 50).round(1),
    "위험도": np.random.choice(["정상", "경고", "위험"], 50, p=[0.6, 0.3, 0.1]),
})

DANGER_KEYWORDS  = ["위험", "경고", "초과", "드롭", "누락", "오류", "실패", "중단", "과부하", "이상"]
WARNING_KEYWORDS = ["저하", "지연", "손실", "감지", "불안정"]

def highlight_log(text):
    for kw in DANGER_KEYWORDS:
        text = text.replace(kw, f':red[**{kw}**]')
    for kw in WARNING_KEYWORDS:
        text = text.replace(kw, f'::orange[**{kw}**]')
    return text

# ── 메인 ──
st.title("🛡️ Admin Dashboard")

# ── 업체 선택 ──
st.subheader("🏢 업체별 조회")
sc1, sc2 = st.columns([1, 2])
with sc1:
    company_search = st.text_input("업체 검색", placeholder="업체명 입력...")
with sc2:
    filtered_companies = [c for c in company_data.keys() if not company_search or company_search in c]
    selected = st.selectbox("업체 선택", filtered_companies if filtered_companies else list(company_data.keys()))

data     = company_data[selected]
defaults = default_scoring[selected]
perf     = perf_by_company[selected]

total_sessions  = sum(v["sessions"]  for v in company_data.values())
total_events    = sum(v["events"]    for v in company_data.values())
avg_score_total = round(sum(v["avg_score"] for v in company_data.values()) / len(company_data))
total_blacklist = sum(v["blacklist"] for v in company_data.values())

st.markdown("**전체 현황**")
tc1, tc2, tc3, tc4 = st.columns(4)
tc1.metric("전체 활성 세션",   f"{total_sessions}건")
tc2.metric("전체 위험 이벤트", f"{total_events}건")
tc3.metric("전체 평균 점수",   f"{avg_score_total}점")
tc4.metric("전체 블랙리스트",  f"{total_blacklist}명")

st.markdown(f"**{selected} 현황**")
col1, col2, col3, col4 = st.columns(4)
col1.metric("활성 세션",   f"{data['sessions']}건")
col2.metric("위험 이벤트", f"{data['events']}건")
col3.metric("평균 점수",   f"{data['avg_score']}점")
col4.metric("블랙리스트",  f"{data['blacklist']}명")

# ── 업체별 차트 (선택 업체 강조, 나머지 회색) ──
companies_list = list(company_data.keys())
avg_scores  = [v["avg_score"] for v in company_data.values()]
event_counts = [v["events"]   for v in company_data.values()]

score_colors = ["#534AB7" if c == selected else "#CCCCCC" for c in companies_list]
event_colors = ["#E24B4A" if c == selected else "#CCCCCC" for c in companies_list]

cc1, cc2 = st.columns(2)
with cc1:
    fig1 = go.Figure(go.Bar(
        x=companies_list, y=avg_scores,
        marker_color=score_colors,
        text=avg_scores, textposition="outside",
    ))
    fig1.update_layout(title="업체별 평균 안전 점수", height=220, margin=dict(t=40, b=20),
                       showlegend=False, yaxis=dict(range=[0, 100]))
    st.plotly_chart(fig1, use_container_width=True)

with cc2:
    fig2 = go.Figure(go.Bar(
        x=companies_list, y=event_counts,
        marker_color=event_colors,
        text=event_counts, textposition="outside",
    ))
    fig2.update_layout(title="업체별 위험 이벤트 수", height=220, margin=dict(t=40, b=20),
                       showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── 성능 + 스코어링 ──
col5, col6 = st.columns(2)

with col5:
    st.subheader("📈 시스템 성능 통계")
    pm1, pm2, pm3, pm4 = st.columns(4)
    pm1.metric("YOLO mAP",  str(perf["yolo_map"]))
    pm2.metric("YOLO FPS",  str(perf["yolo_fps"]))
    pm3.metric("Depth mAP", str(perf["depth_map"]))
    pm4.metric("Depth FPS", str(perf["depth_fps"]))

    perf_data = pd.DataFrame({
        "시간": [f"14:{30+i:02d}" for i in range(10)],
        "YOLO FPS": np.random.uniform(perf["yolo_fps"]-2, perf["yolo_fps"]+2, 10).round(1),
        "추론 지연(ms)": np.random.uniform(38, 55, 10).round(1),
    })

    fig_fps = go.Figure()
    fig_fps.add_trace(go.Scatter(
        x=perf_data["시간"], y=perf_data["YOLO FPS"],
        name="YOLO FPS", line=dict(color="#534AB7", width=2), mode="lines+markers"
    ))
    fig_fps.add_trace(go.Scatter(
        x=perf_data["시간"], y=perf_data["추론 지연(ms)"],
        name="추론 지연(ms)", line=dict(color="#E24B4A", width=2, dash="dot"), mode="lines+markers",
        yaxis="y2"
    ))
    fig_fps.update_layout(
        title="실시간 FPS & 추론 지연",
        height=220, margin=dict(t=40, b=20),
        yaxis=dict(title="FPS"),
        yaxis2=dict(title="지연(ms)", overlaying="y", side="right"),
        legend=dict(orientation="h", y=-0.3),
    )
    st.plotly_chart(fig_fps, use_container_width=True)

    perf_summary = pd.DataFrame({
        "모델": ["YOLOv8", "Depth Anything V2"],
        "mAP": [perf["yolo_map"], perf["depth_map"]],
        "평균 FPS": [perf["yolo_fps"], perf["depth_fps"]],
        "상태": ["정상", "정상"],
    })
    st.dataframe(perf_summary, use_container_width=True, hide_index=True)

    nm1, nm2 = st.columns(2)
    nm1.metric("응답 지연",    perf["latency"])
    nm2.metric("패킷 손실률", perf["packet_loss"])

with col6:
    st.subheader("⚙️ 스코어링 기준값 설정")
    st.slider("급출발 감점",          0, 30,  defaults["급출발 감점"])
    st.slider("급제동 감점",          0, 30,  defaults["급제동 감점"])
    st.slider("근접+급가속 감점",     0, 30,  defaults["근접+급가속 감점"])
    st.slider("근접+과속 감점",       0, 30,  defaults["근접+과속 감점"])
    st.slider("블랙리스트 기준점",    0, 100, defaults["블랙리스트 기준점"])
    st.slider("Green 등급 최소점수",  0, 100, defaults["Green 등급 최소점수"])
    if st.button("💾 저장", use_container_width=True, type="primary"):
        st.success(f"**{selected}** 스코어링 기준값이 저장되었습니다!")

st.divider()

# ── 병목 구간 ──
st.subheader("🔍 프레임 처리 병목 구간 조회")
color_map = {"정상": "#1D9E75", "경고": "#EF9F27", "위험": "#E24B4A"}
fig_scatter = px.scatter(
    bottleneck_data, x="추론 시간(ms)", y="전송 지연(ms)",
    color="위험도", color_discrete_map=color_map,
    title="추론 시간 vs 전송 지연",
)
fig_scatter.update_traces(marker=dict(size=8, opacity=0.7))
fig_scatter.update_layout(height=300, margin=dict(t=40, b=20))
st.plotly_chart(fig_scatter, use_container_width=True)

bc1, bc2 = st.columns(2)
with bc1:
    fig_hist = px.histogram(bottleneck_data, x="추론 시간(ms)", title="추론 시간 분포", nbins=15,
                            color_discrete_sequence=["#534AB7"])
    fig_hist.update_layout(height=220, margin=dict(t=40, b=20))
    st.plotly_chart(fig_hist, use_container_width=True)
with bc2:
    danger_counts = bottleneck_data["위험도"].value_counts().reset_index()
    danger_counts.columns = ["위험도", "count"]
    fig_pie = px.pie(danger_counts, names="위험도", values="count",
                     title="프레임 위험도 분포",
                     color="위험도", color_discrete_map=color_map)
    fig_pie.update_layout(height=220, margin=dict(t=40, b=20))
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# ── 시스템 로그 ──
st.subheader("📋 최근 시스템 로그")
fc1, fc2, fc3, fc4 = st.columns([2, 1, 1, 1])
with fc1:
    search = st.text_input("검색", placeholder="키워드 검색...")
with fc2:
    log_type_filter = st.selectbox("유형 필터", ["전체", "시스템", "네트워크"])
with fc3:
    date_from = st.date_input("From", value=None)
with fc4:
    date_to = st.date_input("To", value=None)

filtered_logs = system_logs.copy()
if search:
    filtered_logs = [l for l in filtered_logs if search in l["설명"] or search in l["유형"]]
if log_type_filter != "전체":
    filtered_logs = [l for l in filtered_logs if l["유형"] == log_type_filter]

# 로그 테이블 — st.columns로 렌더링 (HTML 대신)
header1, header2, header3 = st.columns([2, 1, 4])
header1.markdown("**시간**")
header2.markdown("**유형**")
header3.markdown("**설명**")

for log in filtered_logs:
    c1, c2, c3 = st.columns([2, 1, 4])
    with c1:
        st.caption(log["시간"])
    with c2:
        if log["유형"] == "시스템":
            st.markdown(":blue[**시스템**]")
        else:
            st.markdown(":green[**네트워크**]")
    with c3:
        desc = log["설명"]
        for kw in DANGER_KEYWORDS:
            desc = desc.replace(kw, f":red[**{kw}**]")
        for kw in WARNING_KEYWORDS:
            desc = desc.replace(kw, f":orange[**{kw}**]")
        st.markdown(desc)
