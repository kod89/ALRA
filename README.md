# AI Literature Research Assistant

의료 분야 문헌 조사를 빠르게 수행할 수 있도록 만든 연구지원용 툴입니다.  
연구 주제를 입력하면 PubMed에서 관련 논문을 수집하고, 관련도 기반으로 핵심 문헌을 정렬한 뒤 다음 내용을 함께 제공합니다.

- Top 논문 리스트
- 연구 흐름 Timeline
- Research Gap
- 문헌조사 브리프


## Demo Overview

현재 서비스는 다음 흐름으로 동작합니다.

1. 사용자가 한국어 연구 주제를 입력
2. 내부적으로 검색어를 정제하고 영어 biomedical 검색 키워드로 확장
3. PubMed에서 후보 논문을 넓게 수집
4. biomedical 특화 임베딩 모델로 관련도를 재정렬
5. 핵심 논문, 연구 흐름, 연구 공백, 브리프를 생성


## Project Structure

```text
service/
├── app/
│   ├── main_ALRA.py
│   ├── model_service.py
│   ├── schemas.py
│   ├── auth.py
│   ├── error_handlers.py
│   ├── logger_config.py
│   └── middleware.py
├── frontend/
│   └── app_ALRA.py
├── ALRA01.ipynb
├── requirements.txt
└── README.md
```

주요 파일 설명:

- `app/main_ALRA.py`
  - FastAPI 서버 엔트리포인트
  - `/health`, `/predict` 제공
- `app/model_service.py`
  - 검색어 정교화, PubMed 수집, 재랭킹, 브리프 생성 담당
- `frontend/app_ALRA.py`
  - Streamlit UI

## Requirements

프로젝트는 아래 패키지들을 사용합니다.

- `fastapi`
- `uvicorn`
- `streamlit`
- `requests`
- `torch`
- `transformers`
- `sentence-transformers`

설치는 `requirements.txt`로 진행합니다.

## How to Run

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

최초 실행 시에는 Hugging Face 모델 다운로드가 발생할 수 있어 시간이 다소 걸릴 수 있습니다.

### 2. FastAPI 서버 실행

터미널 창 열고 (window : powershell 실행) 
```bash
uvicorn app.main_ALRA:app --reload
```

실행 후 Swagger UI:

```text
http://localhost:8000/docs
```

현재는 API Key 없이 `POST /predict`를 바로 테스트할 수 있습니다.

### 3. Streamlit 프론트엔드 실행

다른 터미널에서 실행:

```bash
streamlit run frontend/app_ALRA.py
```

실행 후 브라우저 접속:

```text
http://localhost:8501
```

## Example Queries

현재 앱에는 아래 예시 질의가 기본 설정되어 있습니다.

- `뇌종양 치료 관련 최신 연구 동향과 향후 연구 공백`
- `퇴행성 척추질환 치료 연구의 최근 흐름과 핵심 쟁점`
- `뇌혈관 질환 치료 관련 주요 논문과 연구 공백`

이 외에도 다음과 같은 질문으로 테스트할 수 있습니다.

- `glioblastoma surgery outcome and prognosis`
- `cerebral aneurysm endovascular treatment review`
- `degenerative cervical myelopathy prognosis and treatment`
- `spine surgery complication risk factors`

## Current Strengths

- 한국어 질의를 그대로 입력할 수 있음
- PubMed 기반 실제 문헌 검색
- biomedical 특화 임베딩 모델을 사용한 재랭킹
- 단순 논문 목록이 아니라 연구 흐름과 연구 공백까지 함께 제공
- 브리프 마지막 섹션에서 실행 제안 + 기획 시사점을 생성

## Current Limitations

아직 개선이 필요한 부분도 분명히 있습니다.

- pretrained model만 활용
- 검색어 확장 사전이 신경외과 중심으로 제한적임
- PubMed 검색 결과 품질이 질의 표현 방식에 영향을 많이 받음
- 브리프 생성이 완전 생성형 LLM이 아니라 규칙 기반 + 요약형 조합이라 문체가 다소 고정적일 수 있음 (추후 LLM 연결 가능)
- 논문 수집 소스가 현재 PubMed 하나로 제한됨
- 검색 결과가 적을 때는 연구 공백과 제안의 정밀도가 떨어질 수 있음

## Future Improvements

추후 다음과 같은 방향으로 확장할 수 있습니다.

### 1. 검색 품질 고도화

- 신경외과/종양/뇌혈관/척추 분야별 검색어 확장 사전 강화
- PubMed MeSH term 활용
- Cross-encoder 기반 재랭커 추가

### 2. 문헌 소스 확장

- Semantic Scholar
- Europe PMC
- Crossref
- ClinicalTrials.gov

### 3. 브리프 품질 향상

- 제안 섹션을 질환별 템플릿과 연결
- 연구 설계, 비교군, 임상 적용성, 평가 지표 제안 강화
- PDF/Word 형태 브리프 다운로드 지원

### 4. 사용자 경험 개선

- DOI 링크 버튼 개선
- 검색 실패 시 추천 검색어 자동 제안
- 질의 히스토리 및 결과 저장
- 결과 복사/내보내기 기능 강화


## Notes

- 본 프로젝트는 연구지원 목적의 시연용 앱이며, 의료적 판단을 대체하지 않습니다.
- 검색 결과 품질은 입력 질의의 구체성, PubMed 메타데이터 품질, 모델 성능에 영향을 받습니다.

<img width="1840" height="870" alt="alra001" src="https://github.com/user-attachments/assets/d917baf6-3295-43f3-aa49-3975339f9ff9" />
<img width="1840" height="870" alt="alra002" src="https://github.com/user-attachments/assets/df4f8106-876a-4e62-803e-d8b9a709918a" />
