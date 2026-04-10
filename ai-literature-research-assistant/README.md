# AI Literature Research Assistant

Biomedical R&D research support demo built as a single Streamlit application.

This portfolio version helps users:
- retrieve biomedical literature from PubMed
- prioritize the most relevant papers
- summarize research progression over time
- identify key research gaps
- generate a draft literature review brief

When live PubMed retrieval is unavailable, the app automatically falls back to an internal demo corpus so reviewers can still test the workflow.

## Why This Project Fits Biomedical R&D

This app is designed for workflows such as:
- biomaterial and formulation trend review
- medical device prior-art investigation
- literature triage for research planning
- evidence collection for proposal drafting

Examples aligned with the target role:
- hyaluronic acid filler stability and formulation trends
- collagen-based biomaterials for medical devices
- tissue compatibility research for aesthetic biomaterials

## Project Structure

```text
ai-literature-research-assistant/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── config.toml
└── alra/
    ├── __init__.py
    ├── model_service.py
    └── sample_corpus.py
```

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL shown in the terminal.

## Deploy on Streamlit Community Cloud

1. Push this folder to a public GitHub repository.
2. Go to Streamlit Community Cloud.
3. Create a new app from the repository.
4. Set the app entrypoint to `app.py`.
5. Deploy.

Recommended references:
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization
- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy

## Suggested Demo Queries

- 히알루론산 필러의 안정성 및 제형 연구 동향
- 콜라겐 기반 생체재료의 의료기기 적용 동향
- 미용 성형용 생체재료의 조직 적합성 연구

## Notes

- This portfolio version removes API authentication and backend server setup to reduce friction for reviewers.
- The original course version with FastAPI and API key authentication is preserved separately in the parent project.
