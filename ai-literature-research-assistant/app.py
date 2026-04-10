from __future__ import annotations

import streamlit as st

from alra import SOURCE_LABELS, load_model, predict

st.set_page_config(
    page_title="AI Literature Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

EXAMPLE_QUERIES = [
    "히알루론산 필러의 안정성 및 제형 연구 동향",
    "콜라겐 기반 생체재료의 의료기기 적용 동향",
    "미용 성형용 생체재료의 조직 적합성 연구",
]

SECTION_LABELS = {
    "korean": {
        "hero_kicker": "Biomedical R&D Research Support Tool",
        "hero_title": "AI Literature Research Assistant",
        "hero_subtitle": "의료·바이오 문헌을 빠르게 수집하고, 핵심 논문·연구 흐름·연구 공백·브리프 초안까지 한 번에 정리합니다.",
        "audience": "추천 사용자: 소재 연구원, 의료기기 R&D, 생체재료 개발, 기술기획/사업개발",
        "sidebar_title": "리서치 설정",
        "years": "조사 기간(년)",
        "max_papers": "상위 논문 수",
        "domain": "도메인",
        "language": "결과 언어",
        "mode_title": "데이터 모드",
        "mode_body": "PubMed 실시간 조회를 우선 사용하고, 실패 시 데모용 샘플 문헌으로 자동 전환됩니다.",
        "input_title": "연구 주제 입력",
        "input_help": "예: 콜라겐 기반 생체재료의 조직 적합성, 히알루론산 필러의 안정성 및 제형 연구",
        "run_button": "문헌 조사 시작",
        "example_title": "빠른 예시 질의",
        "summary_title": "결과 요약",
        "metric_papers": "수집 논문 수",
        "metric_source": "데이터 출처",
        "metric_gaps": "대표 연구 공백",
        "metric_latest": "최신 논문 연도",
        "papers_title": "Top 논문 리스트",
        "timeline_title": "연구 흐름 Timeline",
        "gaps_title": "Research Gap",
        "brief_title": "문헌조사 브리프",
        "download_button": "브리프 다운로드",
        "download_file": "alra_brief.txt",
        "status": "문헌을 수집하고 브리프를 생성하는 중입니다...",
        "source_prefix": "문헌 출처",
        "relevance": "관련도 점수",
        "journal": "저널",
        "year": "연도",
        "doi": "DOI",
        "abstract": "초록 미리보기",
        "doi_link": "DOI 링크 열기",
        "footer": "Portfolio build for biomedical R&D research support.",
    },
    "english": {
        "hero_kicker": "Biomedical R&D Research Support Tool",
        "hero_title": "AI Literature Research Assistant",
        "hero_subtitle": "Retrieve biomedical literature, prioritize key papers, summarize research progression, highlight gaps, and generate a draft brief in one workflow.",
        "audience": "Recommended for biomaterials R&D, medical device teams, formulation research, and strategy planning",
        "sidebar_title": "Research Settings",
        "years": "Lookback window (years)",
        "max_papers": "Top papers to show",
        "domain": "Domain",
        "language": "Output language",
        "mode_title": "Data Mode",
        "mode_body": "The app first attempts live PubMed retrieval and automatically falls back to a demo sample corpus when needed.",
        "input_title": "Research Topic",
        "input_help": "Example: tissue compatibility of collagen-based biomaterials, formulation stability of hyaluronic acid fillers",
        "run_button": "Run Literature Review",
        "example_title": "Quick Example Queries",
        "summary_title": "Result Summary",
        "metric_papers": "Retrieved papers",
        "metric_source": "Data source",
        "metric_gaps": "Research gaps",
        "metric_latest": "Latest year",
        "papers_title": "Top Papers",
        "timeline_title": "Research Timeline",
        "gaps_title": "Research Gaps",
        "brief_title": "Literature Review Brief",
        "download_button": "Download Brief",
        "download_file": "alra_brief.txt",
        "status": "Retrieving literature and generating the brief...",
        "source_prefix": "Literature source",
        "relevance": "Relevance score",
        "journal": "Journal",
        "year": "Year",
        "doi": "DOI",
        "abstract": "Abstract preview",
        "doi_link": "Open DOI link",
        "footer": "Portfolio build for biomedical R&D research support.",
    },
}


@st.cache_resource
def get_service_bundle():
    return load_model()


def set_example_query(value: str) -> None:
    st.session_state["query_input"] = value


def render_hero(copy: dict[str, str]) -> None:
    st.markdown(
        """
        <style>
        .hero-card {
            padding: 1.4rem 1.6rem;
            border: 1px solid rgba(46, 69, 58, 0.15);
            background: linear-gradient(135deg, rgba(240,245,241,0.95), rgba(250,251,248,0.98));
            border-radius: 20px;
            margin-bottom: 1rem;
        }
        .hero-kicker {
            color: #2f5a46;
            font-size: 0.85rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }
        .hero-title {
            color: #18392a;
            font-size: 2.2rem;
            font-weight: 800;
            margin-top: 0.4rem;
            margin-bottom: 0.4rem;
        }
        .hero-body {
            color: #2d4238;
            font-size: 1rem;
            line-height: 1.6;
            margin-bottom: 0.3rem;
        }
        .panel-card {
            border: 1px solid rgba(46, 69, 58, 0.12);
            border-radius: 16px;
            padding: 1rem 1rem 0.8rem 1rem;
            background: rgba(251, 252, 250, 0.95);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="hero-kicker">{copy['hero_kicker']}</div>
            <div class="hero-title">{copy['hero_title']}</div>
            <div class="hero-body">{copy['hero_subtitle']}</div>
            <div class="hero-body"><strong>{copy['audience']}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(copy: dict[str, str]) -> dict:
    with st.sidebar:
        st.header(copy["sidebar_title"])
        years = st.slider(copy["years"], min_value=1, max_value=15, value=5)
        max_papers = st.slider(copy["max_papers"], min_value=5, max_value=20, value=8)
        domain = st.selectbox("Domain", ["bio/medical", "biomedical", "medicine", "pharma"], index=0)
        language = st.selectbox(copy["language"], ["korean", "english"], index=0)
        st.divider()
        st.caption(copy["mode_title"])
        st.info(copy["mode_body"])
    return {
        "years": years,
        "max_papers": max_papers,
        "domain": domain,
        "language": language,
    }


def render_examples(copy: dict[str, str]) -> None:
    st.subheader(copy["example_title"])
    cols = st.columns(3)
    for col, value in zip(cols, EXAMPLE_QUERIES):
        with col:
            st.button(value, use_container_width=True, on_click=set_example_query, args=(value,))


def render_metrics(result: dict, copy: dict[str, str]) -> None:
    stats = result["stats"]
    cols = st.columns(4)
    cols[0].metric(copy["metric_papers"], stats["paper_count"])
    cols[1].metric(copy["metric_source"], result["source_label"])
    cols[2].metric(copy["metric_gaps"], stats["gap_count"])
    cols[3].metric(copy["metric_latest"], stats["latest_year"] or "-")


def render_papers(result: dict, copy: dict[str, str]) -> None:
    st.subheader(copy["papers_title"])
    st.caption(f"{copy['source_prefix']}: {result['source_label']}")
    for idx, paper in enumerate(result["papers"], start=1):
        with st.container(border=True):
            st.markdown(f"**{idx}. {paper['title']}**")
            meta_cols = st.columns([1.1, 1.2, 0.8, 1.1])
            meta_cols[0].write(f"**{copy['relevance']}**  \n{paper['relevance_score']}")
            meta_cols[1].write(f"**{copy['journal']}**  \n{paper.get('journal') or 'N/A'}")
            meta_cols[2].write(f"**{copy['year']}**  \n{paper.get('year') or 'N/A'}")
            if paper.get("doi_url"):
                meta_cols[3].markdown(f"[{copy['doi_link']}]({paper['doi_url']})")
            else:
                meta_cols[3].write("N/A")
            st.write(f"**{copy['abstract']}**")
            st.write(paper["abstract_preview"])


def render_insights(result: dict, copy: dict[str, str]) -> None:
    st.subheader(copy["timeline_title"])
    for line in result["timeline_summary"]:
        st.write(f"- {line}")

    st.divider()
    st.subheader(copy["gaps_title"])
    for gap in result["research_gaps"]:
        st.write(f"- {gap}")


def render_brief(result: dict, copy: dict[str, str]) -> None:
    st.subheader(copy["brief_title"])
    st.text_area(copy["brief_title"], value=result["report_draft"], height=320, label_visibility="collapsed")
    st.download_button(
        copy["download_button"],
        result["report_draft"],
        file_name=copy["download_file"],
        use_container_width=True,
    )


def main() -> None:
    if "query_input" not in st.session_state:
        st.session_state["query_input"] = EXAMPLE_QUERIES[0]

    default_language = "korean"
    copy = SECTION_LABELS[default_language]
    render_hero(copy)
    settings = render_sidebar(copy)
    copy = SECTION_LABELS[settings["language"]]

    render_examples(copy)
    st.subheader(copy["input_title"])
    with st.form("research_form", border=True):
        query = st.text_area(
            copy["input_title"],
            key="query_input",
            height=140,
            help=copy["input_help"],
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button(copy["run_button"], use_container_width=True)

    if submitted:
        bundle = get_service_bundle()
        with st.spinner(copy["status"]):
            st.session_state["portfolio_result"] = predict(
                bundle,
                {
                    "query": query,
                    "years": settings["years"],
                    "max_papers": settings["max_papers"],
                    "domain": settings["domain"],
                    "language": settings["language"],
                },
            )

    result = st.session_state.get("portfolio_result")
    if result:
        copy = SECTION_LABELS[result["language"]]
        st.divider()
        st.subheader(copy["summary_title"])
        render_metrics(result, copy)
        col_left, col_right = st.columns([1.35, 1.0], gap="large")
        with col_left:
            render_papers(result, copy)
        with col_right:
            render_insights(result, copy)
        st.divider()
        render_brief(result, copy)

    st.caption(copy["footer"])


if __name__ == "__main__":
    main()
