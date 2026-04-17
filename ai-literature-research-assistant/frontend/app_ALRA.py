"""
ALRA Streamlit frontend.
"""
import requests
import streamlit as st

API_BASE = "http://localhost:8000"
DEFAULT_QUERY = "뇌종양 치료 관련 최신 연구 동향과 향후 연구 공백"
EXAMPLE_QUERIES = [
    "뇌종양 치료 관련 최신 연구 동향과 향후 연구 공백",
    "퇴행성 척추질환 치료 연구의 최근 흐름과 핵심 쟁점",
    "뇌혈관 질환 치료 관련 주요 논문과 연구 공백",
]
SOURCE_LABELS = {
    "pubmed": "PubMed 실시간 수집",
    "fallback_sample": "데모용 샘플 문헌",
}

st.set_page_config(
    page_title="AI Literature Research Assistant",
    page_icon="📚",
    layout="wide",
)


def call_api(payload: dict):
    try:
        response = requests.post(
            f"{API_BASE}/predict",
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("🔌 서버에 연결할 수 없습니다. FastAPI 서버를 먼저 실행하세요.")
        return None
    except requests.exceptions.HTTPError as exc:
        if exc.response.status_code == 422:
            try:
                detail = exc.response.json().get("detail")
                st.error(f"입력 검증 오류: {detail}")
            except Exception:
                st.error("입력 검증 오류가 발생했습니다.")
        else:
            st.error(f"서버 오류가 발생했습니다. (HTTP {exc.response.status_code})")
        return None
    except Exception as exc:
        st.error(f"알 수 없는 오류가 발생했습니다: {type(exc).__name__}")
        return None


def fetch_health():
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def set_example_query(value: str):
    st.session_state["query_input"] = value


with st.sidebar:
    st.header("설정")
    years = st.slider("최근 조사 연도", min_value=1, max_value=15, value=5)
    max_papers = st.slider("수집 논문 수", min_value=5, max_value=30, value=10)
    st.divider()

    health = fetch_health()
    if health and health.get("status") == "healthy":
        st.success("🟢 서버 연결됨")
        st.caption(f"서비스: {health.get('model', 'N/A')}")
        st.caption(f"랭킹: {health.get('ranking_mode', 'N/A')}")
    elif health:
        st.warning("🟡 서비스 로딩 중...")
    else:
        st.error("🔴 서버 연결 실패")

    st.divider()
    st.caption("AI Literature Research Assistant")


st.title("AI Literature Research Assistant")
st.write("의료 연구 관련 주제를 입력하면 관련 문헌 조사 브리프를 생성합니다.")

if "query_input" not in st.session_state:
    st.session_state["query_input"] = DEFAULT_QUERY

st.subheader("빠른 예시 질문")
cols = st.columns(3)
for col, example in zip(cols, EXAMPLE_QUERIES):
    with col:
        st.button(example, use_container_width=True, on_click=set_example_query, args=(example,))

query = st.text_area(
    "연구 주제 또는 연구 질문",
    key="query_input",
    height=120,
    help="예: 뇌종양, 척추질환, 뇌혈관 질환 등 신경외과 연구와 관련된 주제를 입력하세요.",
)

if st.button("문헌 조사 시작", type="primary", use_container_width=True):
    payload = {
        "query": query,
        "years": years,
        "max_papers": max_papers,
    }
    with st.spinner("문헌을 수집하고 브리프를 생성하는 중입니다..."):
        result = call_api(payload)
    if result:
        st.session_state["alra_result"] = result


result = st.session_state.get("alra_result")
if result:
    col1, col2 = st.columns([1.3, 1.0])

    with col1:
        st.subheader("Top 논문 리스트")
        st.caption(f"문헌 출처: {SOURCE_LABELS.get(result['source'], result['source'])}")
        if not result["papers"]:
            st.warning("관련성이 높은 PubMed 문헌을 찾지 못했습니다.")
            st.caption("질환명, 치료법, 수술명, 예후 지표를 포함해 더 구체적인 검색어로 다시 시도해 보세요.")
        else:
            for index, paper in enumerate(result["papers"], start=1):
                with st.expander(f"{index}. {paper['title']}"):
                    st.write(f"**관련도 점수:** {paper['relevance_score']}")
                    st.write(f"**저널:** {paper.get('journal') or 'N/A'}")
                    st.write(f"**연도:** {paper.get('year') or 'N/A'}")
                    doi = paper.get("doi") or "N/A"
                    st.write(f"**DOI:** {doi}")
                    st.write(f"**초록 미리보기:** {paper['abstract_preview'] or '초록 정보 없음'}")

    with col2:
        st.subheader("연구 흐름 Timeline")
        for line in result["timeline_summary"]:
            st.write(f"- {line}")

        st.subheader("Research Gap")
        for gap in result["research_gaps"]:
            st.write(f"- {gap}")

    st.subheader("문헌조사 브리프")
    st.text_area("보고서 초안", value=result["report_draft"], height=320)
