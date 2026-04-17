"""
ALRA model service.

검색 품질 개선 포인트:
- 샘플 코퍼스 제거
- PubMed 검색 후보군 확대 후 재랭킹
- 한국어 질의의 규칙 기반 검색어 확장
- biomedical 특화 임베딩 모델 사용
- 문장 전체 번역 대신 필요할 때만 번역 fallback 사용
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any

import requests
import torch
from sentence_transformers import SentenceTransformer, util
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_SUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
PUBMED_ABSTRACT_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

KOREAN_TO_ENGLISH = {
    "뇌종양": ["brain tumor", "glioma", "glioblastoma"],
    "교모세포종": ["glioblastoma"],
    "신경교종": ["glioma"],
    "뇌혈관": ["cerebrovascular", "intracranial aneurysm", "stroke"],
    "뇌혈관 질환": ["cerebrovascular disease", "stroke", "intracranial aneurysm"],
    "뇌동맥류": ["intracranial aneurysm", "cerebral aneurysm"],
    "뇌출혈": ["intracerebral hemorrhage", "hemorrhagic stroke"],
    "뇌경색": ["ischemic stroke", "cerebral infarction"],
    "척추": ["spine", "spinal"],
    "척추질환": ["spine disorder", "spinal disease"],
    "퇴행성 척추질환": ["degenerative spine disease", "degenerative cervical myelopathy", "lumbar stenosis"],
    "경추": ["cervical spine"],
    "요추": ["lumbar spine"],
    "디스크": ["intervertebral disc", "disc herniation"],
    "수술": ["surgery", "surgical"],
    "중재시술": ["endovascular", "intervention"],
    "치료": ["treatment", "therapy", "management"],
    "예후": ["prognosis", "outcome"],
    "생존": ["survival"],
    "합병증": ["complication", "adverse event"],
    "재발": ["recurrence"],
    "임상": ["clinical"],
    "영상": ["imaging", "radiology", "MRI"],
    "방사선": ["radiotherapy", "radiation"],
    "항암": ["chemotherapy"],
    "면역": ["immunotherapy"],
    "연구 동향": ["review", "trend"],
    "최신": ["recent"],
}

QUERY_FILLER_PATTERNS = [
    r"최신",
    r"연구 동향",
    r"동향",
    r"핵심 쟁점",
    r"향후 연구 공백",
    r"연구 공백",
    r"관련",
    r"주요 논문",
    r"최근 흐름",
]

ENGLISH_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "for", "in", "on", "with", "to", "from",
    "related", "recent", "latest", "trend", "trends", "future", "gap", "gaps",
    "research", "study", "studies",
}


def load_model() -> dict[str, Any]:
    """
    biomedical 임베딩 모델 + 번역 fallback 모델을 로드합니다.
    """
    print("ALRA AI 모델 로딩 중 (최초 실행 시 수분 소요)...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"사용 장치: {device}")

    try:
        print("1/2: 번역 fallback 모델(opus-mt-ko-en) 로딩 중...")
        trans_model_name = "Helsinki-NLP/opus-mt-ko-en"
        trans_tokenizer = AutoTokenizer.from_pretrained(trans_model_name)
        trans_model = AutoModelForSeq2SeqLM.from_pretrained(trans_model_name).to(device)

        print("2/2: biomedical 임베딩 모델(S-PubMedBert-MS-MARCO) 로딩 중...")
        embedder = SentenceTransformer("pritamdeka/S-PubMedBert-MS-MARCO", device=device)

        return {
            "service_name": "AI Literature Research Assistant (Biomedical Search)",
            "trans_tokenizer": trans_tokenizer,
            "trans_model": trans_model,
            "embedder": embedder,
            "device": device,
            "ranking_mode": "biomedical-semantic-ranking",
            "report_mode": "retrieval-first-brief",
        }
    except Exception as e:
        print(f"모델 로드 중 심각한 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        raise e


def _translate_query_fallback(query: str, model_bundle: dict[str, Any]) -> str:
    if not any("\uac00" <= char <= "\ud7a3" for char in query):
        return query

    tokenizer = model_bundle["trans_tokenizer"]
    model = model_bundle["trans_model"]
    device = model_bundle["device"]

    inputs = tokenizer(query, return_tensors="pt", padding=True).to(device)
    with torch.no_grad():
        translated_tokens = model.generate(**inputs, max_length=128)
    return tokenizer.decode(translated_tokens[0], skip_special_tokens=True)


def _normalize_query(query: str) -> str:
    cleaned = " ".join(query.split())
    for pattern in QUERY_FILLER_PATTERNS:
        cleaned = re.sub(pattern, " ", cleaned)
    return " ".join(cleaned.split())


def build_search_profile(query_raw: str, model_bundle: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_query(query_raw)
    english_terms: list[str] = []
    matched_keys: list[str] = []

    for key in sorted(KOREAN_TO_ENGLISH, key=len, reverse=True):
        if key in normalized:
            matched_keys.append(key)
            for term in KOREAN_TO_ENGLISH[key]:
                if term not in english_terms:
                    english_terms.append(term)

    if any("\uac00" <= char <= "\ud7a3" for char in normalized) and len(english_terms) < 2:
        translated = _translate_query_fallback(normalized, model_bundle)
        translated_terms = [
            token for token in re.findall(r"[A-Za-z][A-Za-z\-]+", translated.lower())
            if token not in ENGLISH_STOPWORDS and len(token) > 2
        ]
        for term in translated_terms[:8]:
            if term not in english_terms:
                english_terms.append(term)
    else:
        translated = ""

    if not english_terms:
        english_terms = [
            token for token in re.findall(r"[A-Za-z][A-Za-z\-]+", normalized.lower())
            if token not in ENGLISH_STOPWORDS and len(token) > 2
        ]

    ranking_text = " ".join(english_terms) if english_terms else (translated or normalized)
    boolean_terms = []
    for term in english_terms[:8]:
        if " " in term:
            boolean_terms.append(f"\"{term}\"")
        else:
            boolean_terms.append(term)

    return {
        "query_raw": query_raw,
        "query_normalized": normalized,
        "translated": translated,
        "english_terms": english_terms,
        "matched_keys": matched_keys,
        "ranking_text": ranking_text,
        "pubmed_query": " OR ".join(boolean_terms) if boolean_terms else normalized,
    }


def clean_abstract_text(text: str) -> str:
    if not text:
        return ""
    cleaned = " ".join(text.split())
    copyright_patterns = [
        r"Copyright\s+©.*?$",
        r"Copyright\s+\(c\).*?$",
        r"All rights reserved\.?$",
        r"Elsevier B\.V\..*$",
        r"Published by Elsevier.*$",
        r"©\s*\d{4}.*?$",
    ]
    for pattern in copyright_patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
    low_signal_patterns = [
        r"^no abstract available\.?$",
        r"^abstract unavailable\.?$",
        r"^no abstract\.?$",
    ]
    for pattern in low_signal_patterns:
        if re.match(pattern, cleaned, flags=re.IGNORECASE):
            return ""
    return cleaned if len(cleaned) > 40 else ""


def fetch_pubmed_papers(query_profile: dict[str, Any], years: int, max_papers: int) -> list[dict[str, Any]]:
    current_year = datetime.utcnow().year
    min_year = max(current_year - years + 1, 2000)
    candidate_count = max(30, min(max_papers * 5, 80))
    term = f"({query_profile['pubmed_query']}) AND ({min_year}:{current_year}[pdat])"

    try:
        search_resp = requests.get(
            PUBMED_SEARCH_URL,
            params={
                "db": "pubmed",
                "retmode": "json",
                "retmax": candidate_count,
                "sort": "relevance",
                "term": term,
            },
            timeout=20,
        )
        search_resp.raise_for_status()
        id_list = search_resp.json()["esearchresult"].get("idlist", [])
        if not id_list:
            return []

        ids = ",".join(id_list)
        summary_resp = requests.get(
            PUBMED_SUMMARY_URL,
            params={"db": "pubmed", "retmode": "json", "id": ids},
            timeout=20,
        )
        summary_resp.raise_for_status()
        summary_data = summary_resp.json()["result"]

        abstract_resp = requests.get(
            PUBMED_ABSTRACT_URL,
            params={"db": "pubmed", "rettype": "abstract", "retmode": "text", "id": ids},
            timeout=25,
        )
        abstract_resp.raise_for_status()
        abstract_map = _parse_pubmed_abstracts(abstract_resp.text)

        papers: list[dict[str, Any]] = []
        for pmid in id_list:
            record = summary_data.get(pmid, {})
            title = record.get("title", "")
            if not title:
                continue

            doi = next(
                (ai.get("value") for ai in record.get("articleids", []) if ai.get("idtype") == "doi"),
                None,
            )
            year_match = re.search(r"(19|20)\d{2}", record.get("pubdate", ""))
            year = int(year_match.group()) if year_match else None
            abstract = clean_abstract_text(abstract_map.get(pmid) or "")

            papers.append(
                {
                    "title": title,
                    "abstract": abstract,
                    "journal": record.get("fulljournalname") or record.get("source"),
                    "year": year,
                    "doi": doi,
                }
            )
        return papers
    except Exception as e:
        print(f"PubMed API 호출 오류: {e}")
        return []


def _parse_pubmed_abstracts(raw_text: str) -> dict[str, str]:
    blocks = re.split(r"\n\s*\n", raw_text)
    abstract_map: dict[str, str] = {}
    current_pmid = None
    for block in blocks:
        pmid_match = re.search(r"PMID:\s*(\d+)", block)
        if pmid_match:
            current_pmid = pmid_match.group(1)
        if current_pmid:
            cleaned = re.sub(r"PMID:\s*\d+.*$", "", block).strip()
            abstract_map[current_pmid] = cleaned
    return abstract_map


def rank_papers(query_profile: dict[str, Any], papers: list[dict[str, Any]], model_bundle: dict[str, Any]) -> list[dict[str, Any]]:
    if not papers:
        return []

    embedder = model_bundle["embedder"]
    ranking_query = query_profile["ranking_text"] or query_profile["query_raw"]
    query_emb = embedder.encode(ranking_query, convert_to_tensor=True)
    doc_texts = [f"{p.get('title', '')} {p.get('abstract', '')}" for p in papers]
    doc_embs = embedder.encode(doc_texts, convert_to_tensor=True)
    cos_scores = util.cos_sim(query_emb, doc_embs)[0]

    lowered_terms = [term.lower() for term in query_profile["english_terms"][:10]]
    scored = []
    for i, paper in enumerate(papers):
        title_text = (paper.get("title") or "").lower()
        abstract_text = (paper.get("abstract") or "").lower()
        semantic_score = float(cos_scores[i])
        title_overlap = sum(1 for term in lowered_terms if term and term in title_text)
        abstract_overlap = sum(1 for term in lowered_terms if term and term in abstract_text)
        lexical_bonus = min(0.12 * title_overlap + 0.04 * abstract_overlap, 0.45)
        year_bonus = 0.01 * max((paper.get("year") or 2020) - 2020, 0)

        enriched = paper.copy()
        enriched["relevance_score"] = round(semantic_score + lexical_bonus + year_bonus, 4)
        scored.append(enriched)

    return sorted(scored, key=lambda x: x["relevance_score"], reverse=True)


def build_timeline_summary(top_papers: list[dict[str, Any]], model_bundle: dict[str, Any]) -> list[str]:
    if not top_papers:
        return ["관련 문헌을 찾지 못했습니다. 검색어를 더 구체화하거나 영문 핵심 키워드를 포함해 다시 시도해 주세요."]

    grouped: dict[int, list[dict[str, Any]]] = {}
    for paper in top_papers:
        year = paper.get("year") or 0
        grouped.setdefault(year, []).append(paper)

    summary_lines = []
    for year in sorted(grouped, reverse=True)[:5]:
        papers = grouped[year][:2]
        keywords = _extract_keywords(" ".join(f"{p.get('title', '')} {p.get('abstract', '')}" for p in papers))
        representative = papers[0].get("title", "대표 논문 정보 없음")
        summary_lines.append(
            f"{year if year else '연도미상'}: 주요 키워드 {', '.join(keywords[:3])} / 대표 논문: {representative}"
        )
    return summary_lines


def extract_research_gaps(top_papers: list[dict[str, Any]]) -> list[str]:
    if not top_papers:
        return [
            "관련 문헌이 부족해 연구 공백을 자동 추정하지 못했습니다.",
            "질환명, 치료법, 수술명, 임상 결과 지표를 포함해 검색어를 더 구체화해 보세요.",
        ]

    gap_sentences = []
    for paper in top_papers:
        abstract = paper.get("abstract", "")
        for sent in re.split(r"(?<=[.!?])\s+", abstract):
            lowered = sent.lower()
            if any(kw in lowered for kw in ["however", "limitation", "lack", "remain", "future", "needed"]):
                gap_sentences.append(sent.strip())

    if not gap_sentences:
        return [
            "기존 치료법과의 직접 비교 및 장기 추적 데이터가 더 필요합니다.",
            "실제 임상 환경을 반영한 전향적 검증 연구가 보강될 필요가 있습니다.",
            "하위 환자군과 예후 지표를 세분화한 분석이 추가로 요구됩니다.",
        ]

    cleaned = []
    for sent in gap_sentences:
        if sent and sent not in cleaned:
            cleaned.append(sent)
    return cleaned[:3]


def generate_report_draft(
    query: str,
    top_papers: list[dict[str, Any]],
    timeline: list[str],
    gaps: list[str],
    source: str,
) -> str:
    if not top_papers:
        recommendations = build_actionable_recommendations(query, gaps, top_papers)
        return (
            f"[AI 기반 문헌조사 브리프]\n주제: {query}\n출처: {source}\n\n"
            "1. 검색 결과 요약\n- 현재 검색 조건으로는 관련성이 높은 문헌을 충분히 확보하지 못했습니다.\n\n"
            "2. 개선 제안\n"
            + "\n".join(f"- {item}" for item in recommendations)
        )

    titles = [p["title"] for p in top_papers[:3]]
    recommendations = build_actionable_recommendations(query, gaps, top_papers)
    return (
        f"[AI 기반 문헌조사 브리프]\n주제: {query}\n출처: {source}\n\n"
        f"1. 최신 연구 흐름\n" + "\n".join(f"  * {line}" for line in timeline) + "\n\n"
        f"2. 핵심 연구\n" + "\n".join(f"- {title}" for title in titles) + "\n\n"
        f"3. 연구 공백\n" + "\n".join(f"- {gap}" for gap in gaps) + "\n\n"
        f"4. 제안\n" + "\n".join(f"- {item}" for item in recommendations)
    )


def predict(model_bundle: dict[str, Any], input_data: dict[str, Any]) -> dict[str, Any]:
    query_raw = input_data["query"]
    query_profile = build_search_profile(query_raw, model_bundle)

    papers = fetch_pubmed_papers(
        query_profile=query_profile,
        years=input_data["years"],
        max_papers=input_data["max_papers"],
    )
    source_key = "pubmed"

    ranked = rank_papers(query_profile, papers, model_bundle)[:input_data["max_papers"]]
    timeline = build_timeline_summary(ranked[:5], model_bundle)
    gaps = extract_research_gaps(ranked[:8])
    report = generate_report_draft(query_raw, ranked, timeline, gaps, "PubMed 실시간 수집")

    results = [
        {
            "title": paper["title"],
            "abstract_preview": _build_abstract_preview(paper.get("abstract", "")),
            "journal": paper.get("journal"),
            "year": paper.get("year"),
            "doi": paper.get("doi"),
            "relevance_score": paper.get("relevance_score", 0.0),
        }
        for paper in ranked
    ]

    return {
        "success": True,
        "query": query_raw,
        "source": source_key,
        "papers": results,
        "timeline_summary": timeline,
        "research_gaps": gaps,
        "report_draft": report,
    }


def _extract_keywords(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z\-]+", text.lower())
    filtered = [token for token in tokens if token not in ENGLISH_STOPWORDS and len(token) > 3]
    counts: dict[str, int] = {}
    for token in filtered:
        counts[token] = counts.get(token, 0) + 1
    return [token for token, _ in sorted(counts.items(), key=lambda item: item[1], reverse=True)]


def _build_abstract_preview(text: str) -> str:
    cleaned = clean_abstract_text(text)
    if not cleaned:
        return "초록 비공개 또는 메타데이터 미제공"
    if len(cleaned) > 280:
        return cleaned[:280].rstrip() + "..."
    return cleaned


def build_actionable_recommendations(
    query: str,
    gaps: list[str],
    top_papers: list[dict[str, Any]],
) -> list[str]:
    if not gaps:
        return [
            "질환명, 치료법, 수술명, 예후 지표를 함께 포함한 검색 전략으로 문헌 범위를 먼저 정교화할 필요가 있습니다.",
            "후속 연구에서는 비교군 설정과 장기 추적 지표를 포함한 설계를 우선 검토하는 것이 바람직합니다.",
            "연구기획 측면에서는 실제 임상 적용성과 평가 지표 표준화를 함께 확보할 수 있는 과제 구조가 경쟁력이 높습니다.",
        ]

    recommendation_templates = [
        (
            "비교 임상/비교군 부족",
            ["compare", "comparison", "comparator", "direct comparison", "기존 치료법과의 직접 비교", "comparative"],
            "기존 치료법 또는 표준치료와의 비교군을 포함한 전향적 비교 연구 설계를 우선 검토할 필요가 있습니다.",
        ),
        (
            "장기 추적/안전성 데이터 부족",
            ["long-term", "safety", "toxicity", "adverse", "장기", "안전성", "독성"],
            "장기 예후와 안전성 데이터를 확보할 수 있도록 추적 관찰 기간을 확장한 후속 연구가 요구됩니다.",
        ),
        (
            "실제 임상 적용성 부족",
            ["real-world", "clinical", "translational", "실제 임상", "임상 환경", "적용성"],
            "실제 환자군과 진료 환경을 반영한 임상 적용성 검증 단계가 추가로 필요합니다.",
        ),
        (
            "하위군/예후 인자 분석 부족",
            ["subgroup", "prognosis", "outcome", "patient group", "예후", "하위군", "환자군"],
            "환자군을 세분화하고 예후 인자를 함께 분석하는 정밀 분석 프레임을 도입할 필요가 있습니다.",
        ),
        (
            "표준화/프로토콜 부족",
            ["protocol", "standard", "guideline", "standardized", "표준화", "프로토콜", "가이드라인"],
            "평가 지표와 연구 프로토콜을 표준화해 후속 연구 간 비교 가능성을 높이는 작업이 중요합니다.",
        ),
    ]

    selected_actions: list[str] = []
    seen_labels: set[str] = set()
    lowered_gaps = [gap.lower() for gap in gaps]

    for label, keywords, action in recommendation_templates:
        if label in seen_labels:
            continue
        if any(keyword.lower() in gap for keyword in keywords for gap in lowered_gaps):
            selected_actions.append(action)
            seen_labels.add(label)
        if len(selected_actions) == 2:
            break

    if len(selected_actions) < 2:
        fallback_actions = [
            "기존 치료법과의 직접 비교 및 장기 추적 데이터를 함께 확보할 수 있는 연구 설계를 우선 검토할 필요가 있습니다.",
            "실제 임상 적용성을 높이기 위해 환자군 세분화와 결과 지표 표준화를 동시에 고려한 후속 연구가 요구됩니다.",
        ]
        for action in fallback_actions:
            if action not in selected_actions:
                selected_actions.append(action)
            if len(selected_actions) == 2:
                break

    lead_titles = [paper.get("title", "") for paper in top_papers[:2] if paper.get("title")]
    if lead_titles:
        planning_line = (
            "연구기획 측면에서는 "
            + ", ".join(lead_titles[:2])
            + " 등에서 드러난 공백을 바탕으로 실제 임상 적용성과 평가 지표 표준화를 함께 확보할 수 있는 과제 구조가 경쟁력이 높습니다."
        )
    else:
        planning_line = (
            "연구기획 측면에서는 실제 임상 적용성과 평가 지표 표준화를 함께 확보할 수 있는 과제 구조가 경쟁력이 높습니다."
        )

    return selected_actions + [planning_line]
