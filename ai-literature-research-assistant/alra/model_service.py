"""
Portfolio ALRA service logic for direct Streamlit execution.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from datetime import datetime
from typing import Any

import requests

from .sample_corpus import SAMPLE_PAPERS

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how", "in",
    "into", "is", "it", "of", "on", "or", "that", "the", "this", "to", "using",
    "with", "기술", "연구", "분석", "개선", "향상", "대한", "및", "에서", "으로",
}

TIMELINE_EXCLUDE_TOKENS = STOPWORDS | {
    "vaccine", "vaccines", "mrna", "rna", "study", "review", "based", "clinical",
    "data", "results", "paper", "platform", "platforms", "development", "recent",
    "advanced", "using", "improving", "improved", "stability", "medical", "biomedical",
    "medicine", "device", "devices", "biomaterial", "biomaterials",
}

SOURCE_LABELS = {
    "pubmed": {
        "korean": "PubMed 실시간 수집",
        "english": "Live PubMed retrieval",
    },
    "fallback_sample": {
        "korean": "데모용 샘플 문헌",
        "english": "Demo sample corpus",
    },
}

DOMAIN_HINTS = {
    "bio/medical": "",
    "pharma": " formulation drug delivery stability",
    "medicine": " clinical device translational safety",
    "biomedical": " biomaterial implant tissue compatibility",
}

PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_SUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
PUBMED_ABSTRACT_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def load_model() -> dict[str, Any]:
    return {
        "service_name": "AI Literature Research Assistant",
        "ranking_mode": "lightweight-keyword-ranking",
        "report_mode": "template-brief-generator",
    }


def predict(model_bundle: dict[str, Any], input_data: dict[str, Any]) -> dict[str, Any]:
    query = input_data["query"]
    years = int(input_data["years"])
    max_papers = int(input_data["max_papers"])
    domain = input_data.get("domain", "bio/medical")
    language = input_data.get("language", "korean")

    try:
        papers = fetch_pubmed_papers(
            query=query,
            years=years,
            max_papers=max_papers,
            domain=domain,
        )
        source = "pubmed" if papers else "fallback_sample"
    except Exception:
        papers = []
        source = "fallback_sample"

    if not papers:
        papers = load_sample_corpus()

    ranked = rank_papers(query, papers)[:max_papers]
    timeline_summary = build_timeline_summary(ranked, language=language)
    research_gaps = extract_research_gaps(ranked, language=language)
    report_draft = generate_report_draft(
        query=query,
        top_papers=ranked,
        timeline_summary=timeline_summary,
        research_gaps=research_gaps,
        source=source,
        language=language,
    )
    latest_year = max((paper.get("year") or 0) for paper in ranked) if ranked else None

    return {
        "success": True,
        "query": query,
        "domain": domain,
        "language": language,
        "source": source,
        "source_label": SOURCE_LABELS[source][language],
        "papers": [
            {
                "title": paper["title"],
                "abstract_preview": _build_abstract_preview(paper.get("abstract", ""), language),
                "journal": paper.get("journal"),
                "year": paper.get("year"),
                "doi": paper.get("doi"),
                "doi_url": f"https://doi.org/{paper['doi']}" if paper.get("doi") else None,
                "relevance_score": paper.get("relevance_score", 0.0),
            }
            for paper in ranked
        ],
        "timeline_summary": timeline_summary,
        "research_gaps": research_gaps,
        "report_draft": report_draft,
        "stats": {
            "paper_count": len(ranked),
            "gap_count": len(research_gaps),
            "latest_year": latest_year,
        },
    }


def fetch_pubmed_papers(query: str, years: int, max_papers: int, domain: str) -> list[dict[str, Any]]:
    current_year = datetime.utcnow().year
    min_year = max(current_year - years + 1, 2000)
    query_with_hint = f"{query}{DOMAIN_HINTS.get(domain, '')}".strip()
    term = f"{query_with_hint} AND ({min_year}:{current_year}[pdat])"

    search_resp = requests.get(
        PUBMED_SEARCH_URL,
        params={
            "db": "pubmed",
            "retmode": "json",
            "retmax": max_papers,
            "sort": "relevance",
            "term": term,
        },
        timeout=15,
    )
    search_resp.raise_for_status()
    id_list = search_resp.json()["esearchresult"].get("idlist", [])
    if not id_list:
        return []

    ids = ",".join(id_list)
    summary_resp = requests.get(
        PUBMED_SUMMARY_URL,
        params={"db": "pubmed", "retmode": "json", "id": ids},
        timeout=15,
    )
    summary_resp.raise_for_status()
    summary_data = summary_resp.json()["result"]

    abstract_resp = requests.get(
        PUBMED_ABSTRACT_URL,
        params={"db": "pubmed", "rettype": "abstract", "retmode": "text", "id": ids},
        timeout=20,
    )
    abstract_resp.raise_for_status()
    abstract_map = _parse_pubmed_abstracts(abstract_resp.text)

    papers: list[dict[str, Any]] = []
    for pmid in id_list:
        record = summary_data.get(pmid, {})
        title = _normalize_whitespace(record.get("title", ""))
        if not title:
            continue

        doi = None
        for article_id in record.get("articleids", []):
            if article_id.get("idtype") == "doi":
                doi = article_id.get("value")
                break

        pubdate = record.get("pubdate", "")
        year_match = re.search(r"(19|20)\d{2}", pubdate)
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


def load_sample_corpus() -> list[dict[str, Any]]:
    return [paper.copy() for paper in SAMPLE_PAPERS]


def rank_papers(query: str, papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    query_tokens = _tokenize(query)
    if not query_tokens:
        return papers

    query_counter = Counter(query_tokens)
    query_norm = math.sqrt(sum(value * value for value in query_counter.values()))
    scored: list[dict[str, Any]] = []

    for paper in papers:
        text = f"{paper.get('title', '')} {paper.get('abstract', '')}"
        doc_tokens = _tokenize(text)
        if not doc_tokens:
            score = 0.0
        else:
            doc_counter = Counter(doc_tokens)
            overlap = sum(query_counter[token] * doc_counter.get(token, 0) for token in query_counter)
            doc_norm = math.sqrt(sum(value * value for value in doc_counter.values()))
            cosine = overlap / (query_norm * doc_norm) if doc_norm else 0.0
            title_bonus = 0.1 * sum(
                1 for token in query_tokens if token in _tokenize(paper.get("title", ""))
            )
            recency_bonus = 0.02 * max((paper.get("year") or 2020) - 2020, 0)
            score = cosine + title_bonus + recency_bonus

        enriched = paper.copy()
        enriched["relevance_score"] = round(score, 4)
        scored.append(enriched)

    return sorted(scored, key=lambda item: item["relevance_score"], reverse=True)


def build_timeline_summary(top_papers: list[dict[str, Any]], language: str) -> list[str]:
    if not top_papers:
        return [
            "관련 문헌이 충분하지 않아 연구 흐름을 생성하지 못했습니다."
            if language == "korean"
            else "Not enough relevant literature was found to build a timeline."
        ]

    grouped: dict[int, list[dict[str, Any]]] = {}
    for paper in top_papers:
        year = paper.get("year") or 0
        grouped.setdefault(year, []).append(paper)

    lines: list[str] = []
    previous_theme = None
    for year in sorted(grouped):
        year_papers = grouped[year]
        joined = " ".join(
            f"{paper.get('title', '')} {paper.get('abstract', '')}" for paper in year_papers
        ).lower()
        theme = _infer_timeline_theme(joined, language)
        keywords = _extract_timeline_keywords(joined)
        representative = max(year_papers, key=lambda paper: paper.get("relevance_score", 0.0))
        title = representative.get("title", "").rstrip(".")
        label = str(year) if year else ("연도 미상" if language == "korean" else "Year N/A")

        if language == "korean":
            details = []
            if previous_theme == theme and keywords:
                details.append(f"핵심 키워드 {', '.join(keywords[:3])}")
            elif keywords:
                details.append(f"주요 키워드 {', '.join(keywords[:3])}")
            if title:
                details.append(f"대표 논문: {title}")
            lines.append(f"{label}: {theme}" + (f" ({' / '.join(details)})" if details else ""))
        else:
            details = []
            if previous_theme == theme and keywords:
                details.append(f"focus keywords: {', '.join(keywords[:3])}")
            elif keywords:
                details.append(f"keywords: {', '.join(keywords[:3])}")
            if title:
                details.append(f"representative paper: {title}")
            lines.append(f"{label}: {theme}" + (f" ({' / '.join(details)})" if details else ""))

        previous_theme = theme

    return lines[:5]


def extract_research_gaps(top_papers: list[dict[str, Any]], language: str) -> list[str]:
    sentences: list[str] = []
    for paper in top_papers:
        for sentence in re.split(r"(?<=[.!?])\s+", paper.get("abstract", "")):
            lowered = sentence.lower()
            if any(
                keyword in lowered
                for keyword in ["limitation", "future work", "remain limited", "missing", "however", "lack"]
            ):
                sentences.append(sentence.strip())

    if not sentences:
        return _default_gaps(language)

    gap_buckets = [
        (
            "독성·안전성 장기 데이터 부족" if language == "korean" else "Insufficient long-term toxicity and safety evidence",
            ["toxicity", "safety", "long-term"],
        ),
        (
            "대규모 비교 임상 및 실증 검증 부족" if language == "korean" else "Limited large-scale comparative and clinical validation",
            ["phase 3", "large-scale", "clinical", "real-world"],
        ),
        (
            "콜드체인 비용 및 운영 최적화 연구 부족" if language == "korean" else "Insufficient cold-chain cost and operations research",
            ["cost", "logistics", "transport", "cold-chain"],
        ),
        (
            "표준화된 평가 지표와 플랫폼 비교 부족" if language == "korean" else "Lack of standardized endpoints and platform comparison",
            ["standard", "comparator", "comparability", "outcome"],
        ),
    ]

    blob = " ".join(sentences).lower()
    found = [label for label, keywords in gap_buckets if any(keyword in blob for keyword in keywords)]
    return found[:4] if found else _default_gaps(language)


def generate_report_draft(
    query: str,
    top_papers: list[dict[str, Any]],
    timeline_summary: list[str],
    research_gaps: list[str],
    source: str,
    language: str,
) -> str:
    top_titles = [paper["title"] for paper in top_papers[:3]]
    top_journals = [paper.get("journal") for paper in top_papers[:3] if paper.get("journal")]
    journal_text = ", ".join(top_journals[:3]) if top_journals else (
        "주요 생의학 저널" if language == "korean" else "major biomedical journals"
    )
    source_label = SOURCE_LABELS[source][language]

    if language == "korean":
        return (
            f"[문헌조사 브리프]\n"
            f"주제: {query}\n"
            f"문헌 출처: {source_label}\n\n"
            f"1. 배경\n"
            f"- 본 주제는 의료·바이오 R&D 기획과 선행연구 정리에 직접 연결되는 이슈입니다.\n"
            f"- 수집된 문헌은 {journal_text}를 중심으로 정리되었습니다.\n\n"
            f"2. 핵심 논문\n"
            + "\n".join(f"- {title}" for title in top_titles)
            + "\n\n3. 연구 흐름\n"
            + "\n".join(f"- {line}" for line in timeline_summary)
            + "\n\n4. 연구 공백\n"
            + "\n".join(f"- {gap}" for gap in research_gaps)
            + "\n\n5. 제안 시사점\n"
            f"- 후속 과제 기획 시 소재 안정성, 임상 검증, 생산 및 적용 가능성을 함께 보는 프레임이 유효합니다.\n"
            f"- 특히 장기 안전성, 비교 임상, 공정 확장성, 규제 적용성을 함께 검토하는 전략이 차별화 포인트가 될 수 있습니다.\n"
        )

    return (
        f"[Literature Review Brief]\n"
        f"Topic: {query}\n"
        f"Literature source: {source_label}\n\n"
        f"1. Background\n"
        f"- This topic is directly relevant to biomedical R&D planning and prior-art review.\n"
        f"- The retrieved literature is concentrated in {journal_text}.\n\n"
        f"2. Key Papers\n"
        + "\n".join(f"- {title}" for title in top_titles)
        + "\n\n3. Research Timeline\n"
        + "\n".join(f"- {line}" for line in timeline_summary)
        + "\n\n4. Research Gaps\n"
        + "\n".join(f"- {gap}" for gap in research_gaps)
        + "\n\n5. Strategic Implications\n"
        f"- Future programs should evaluate material stability, translational validation, and manufacturability together.\n"
        f"- Long-term safety, comparative validation, process scalability, and regulatory readiness can be strong differentiation points.\n"
    )


def clean_abstract_text(text: str) -> str:
    cleaned = _normalize_whitespace(text)
    if not cleaned:
        return ""

    for pattern in [
        r"Copyright\s+©.*?$",
        r"Copyright\s+\(c\).*?$",
        r"All rights reserved\.?$",
        r"Elsevier B\.V\..*$",
        r"Published by Elsevier.*$",
        r"©\s*\d{4}.*?$",
    ]:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()

    cleaned = _normalize_whitespace(cleaned)
    for pattern in [
        r"^no abstract available\.?$",
        r"^abstract unavailable\.?$",
        r"^no abstract\.?$",
    ]:
        if re.match(pattern, cleaned, flags=re.IGNORECASE):
            return ""

    return cleaned if len(cleaned) >= 40 else ""


def _parse_pubmed_abstracts(raw_text: str) -> dict[str, str]:
    blocks = re.split(r"\n\s*\n", raw_text)
    abstract_map: dict[str, str] = {}
    current_pmid = None

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        pmid_match = re.search(r"PMID:\s*(\d+)", block)
        if pmid_match:
            current_pmid = pmid_match.group(1)
        if current_pmid is None:
            continue

        cleaned = re.sub(r"\s+", " ", block)
        cleaned = re.sub(r"PMID:\s*\d+.*$", "", cleaned).strip()
        abstract_map[current_pmid] = clean_abstract_text(cleaned)

    return abstract_map


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9가-힣\-]+", text.lower())
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]


def _normalize_whitespace(text: str) -> str:
    return " ".join((text or "").split())


def _infer_timeline_theme(text: str, language: str) -> str:
    if language == "korean":
        if any(word in text for word in ["freeze", "lyoph", "room-temperature", "ambient"]):
            return "동결건조 및 상온 유통 가능성 검토가 확대됨"
        if any(word in text for word in ["logistics", "cold-chain", "transport", "distribution"]):
            return "콜드체인 최적화와 물류 비용 절감 연구가 두드러짐"
        if any(word in text for word in ["toxicity", "safety", "regulatory", "clinical"]):
            return "안전성 검증과 임상 적용성 점검이 강화됨"
        if any(word in text for word in ["lipid", "lnp", "formulation", "encapsulation"]):
            return "LNP 제형 안정화와 조성 최적화 중심 연구가 활발함"
        if any(word in text for word in ["collagen", "implant", "tissue", "compatibility", "filler"]):
            return "생체재료 적합성과 제형 특성 평가 연구가 확대됨"
        return "의료 R&D 적용 가능성 중심의 후속 연구가 이어짐"

    if any(word in text for word in ["freeze", "lyoph", "room-temperature", "ambient"]):
        return "Exploration of freeze-drying and room-temperature delivery expanded"
    if any(word in text for word in ["logistics", "cold-chain", "transport", "distribution"]):
        return "Cold-chain optimization and logistics cost reduction gained attention"
    if any(word in text for word in ["toxicity", "safety", "regulatory", "clinical"]):
        return "Safety validation and translational feasibility became more prominent"
    if any(word in text for word in ["lipid", "lnp", "formulation", "encapsulation"]):
        return "LNP formulation optimization remained a major theme"
    if any(word in text for word in ["collagen", "implant", "tissue", "compatibility", "filler"]):
        return "Biomaterial compatibility and formulation behavior became more central"
    return "Follow-up studies focused on translational biomedical applicability"


def _extract_timeline_keywords(text: str, limit: int = 3) -> list[str]:
    counter = Counter(
        token for token in _tokenize(text)
        if token not in TIMELINE_EXCLUDE_TOKENS
    )
    return [token for token, _ in counter.most_common(limit)]


def _default_gaps(language: str) -> list[str]:
    if language == "korean":
        return [
            "장기 독성 및 장기 보관 안정성에 대한 후속 검증이 더 필요합니다.",
            "대규모 비교 임상 또는 실제 사용 환경 기반 검증이 부족합니다.",
            "비용 최적화와 규제 적용성을 함께 다룬 연구가 제한적입니다.",
        ]
    return [
        "Additional long-term toxicity and stability evidence is needed.",
        "Large-scale comparative or real-world validation remains limited.",
        "Few studies integrate cost optimization with regulatory applicability.",
    ]


def _build_abstract_preview(text: str, language: str) -> str:
    cleaned = clean_abstract_text(text)
    if not cleaned:
        return (
            "초록 비공개 또는 메타데이터 미제공"
            if language == "korean"
            else "Abstract unavailable or metadata not provided"
        )
    if len(cleaned) > 280:
        return cleaned[:280].rstrip() + "..."
    return cleaned
