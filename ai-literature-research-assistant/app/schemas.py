"""
ALRA request/response schemas.
"""
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class PredictRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=5,
        max_length=300,
        description="문헌 조사를 수행할 연구 주제 또는 연구 질문",
        examples=["뇌종양 치료 관련 최신 연구 동향과 향후 연구 공백"],
    )
    years: int = Field(
        default=5,
        ge=1,
        le=15,
        description="최근 몇 년의 문헌을 우선 조사할지 설정",
    )
    max_papers: int = Field(
        default=10,
        ge=5,
        le=50,
        description="최대 수집 논문 수",
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) < 5:
            raise ValueError("query는 최소 5자 이상이어야 합니다.")
        return cleaned

class PaperResult(BaseModel):
    title: str = Field(description="논문 제목")
    abstract_preview: str = Field(description="초록 미리보기")
    journal: Optional[str] = Field(default=None, description="저널명")
    year: Optional[int] = Field(default=None, description="출판 연도")
    doi: Optional[str] = Field(default=None, description="DOI")
    relevance_score: float = Field(description="관련도 점수")


class PredictResponse(BaseModel):
    success: bool = Field(description="성공 여부")
    query: str = Field(description="입력 연구 주제")
    source: str = Field(description="문헌 수집 출처 (예: pubmed, fallback_sample)")
    papers: list[PaperResult] = Field(description="관련 논문 목록")
    timeline_summary: list[str] = Field(description="연구 흐름 요약")
    research_gaps: list[str] = Field(description="도출된 연구 공백")
    report_draft: str = Field(description="1페이지 문헌 조사 브리프")
