"""
ALRA fallback sample corpus.

PubMed 조회가 실패하거나 결과가 충분하지 않을 때 사용할
의료/바이오 분야 논문 메타데이터 샘플입니다.
"""

SAMPLE_PAPERS = [
    {
        "title": "Lipid nanoparticle engineering strategies for improving mRNA vaccine stability",
        "abstract": (
            "This review summarizes formulation strategies for improving the thermal "
            "stability of mRNA vaccines. It compares ionizable lipids, buffer systems, "
            "and lyophilization methods. Current evidence suggests that excipient "
            "selection and particle size control are major determinants of cold-chain "
            "robustness. However, long-term toxicity data and large-scale stability "
            "comparisons remain limited."
        ),
        "journal": "Advanced Drug Delivery Reviews",
        "year": 2024,
        "doi": "10.1016/j.addr.2024.01.001",
    },
    {
        "title": "Freeze-dried mRNA-LNP formulations for room-temperature distribution",
        "abstract": (
            "Researchers evaluated freeze-dried mRNA lipid nanoparticles for room-temperature "
            "storage. The study reports preserved antigen expression after reconstitution "
            "and highlights the potential for non-frozen logistics. Limitations include "
            "small animal sample sizes and limited real-world transport validation."
        ),
        "journal": "Nature Biomedical Engineering",
        "year": 2025,
        "doi": "10.1038/s41551-025-00021-7",
    },
    {
        "title": "Cold-chain optimization models for vaccine transportation in public health systems",
        "abstract": (
            "This paper presents optimization models for vaccine transportation and storage "
            "with a focus on minimizing spoilage risk and logistics cost. Results show "
            "that route redesign and dynamic temperature monitoring improve resilience. "
            "Future work should validate the model in low-resource settings."
        ),
        "journal": "Vaccine",
        "year": 2023,
        "doi": "10.1016/j.vaccine.2023.05.110",
    },
    {
        "title": "Comparative analysis of stabilizers in thermostable RNA vaccine platforms",
        "abstract": (
            "The authors compare sugar-based and polymer-based stabilizers across RNA vaccine "
            "platforms. Sucrose and trehalose improved short-term thermal resilience, while "
            "polymer systems showed better structural preservation. A key limitation is the "
            "lack of phase 3 clinical comparators."
        ),
        "journal": "Pharmaceutics",
        "year": 2022,
        "doi": "10.3390/pharmaceutics14091876",
    },
    {
        "title": "Translational challenges in room-temperature mRNA vaccine development",
        "abstract": (
            "This perspective reviews translational bottlenecks in room-temperature mRNA "
            "vaccines including regulatory uncertainty, manufacturing scale-up, and safety "
            "monitoring. The field is progressing rapidly, but consensus data on long-term "
            "storage toxicity and platform comparability are still missing."
        ),
        "journal": "Molecular Therapy",
        "year": 2024,
        "doi": "10.1016/j.ymthe.2024.03.014",
    },
    {
        "title": "AI-assisted prioritization of biomedical literature for national R&D planning",
        "abstract": (
            "The study proposes an AI-assisted workflow for biomedical literature triage, "
            "topic clustering, and policy reporting. The system improves review speed, but "
            "its ranking quality depends on metadata completeness and domain-specific prompts."
        ),
        "journal": "Journal of Biomedical Informatics",
        "year": 2023,
        "doi": "10.1016/j.jbi.2023.104321",
    },
    {
        "title": "Recent advances in thermostable vaccine delivery technologies",
        "abstract": (
            "A broad review of thermostable delivery approaches across protein, DNA, and RNA "
            "vaccines. The article highlights drying techniques, encapsulation materials, "
            "and packaging innovation. Evidence is promising, but standardized outcome "
            "measures are not yet widely adopted."
        ),
        "journal": "Trends in Biotechnology",
        "year": 2021,
        "doi": "10.1016/j.tibtech.2021.07.008",
    },
    {
        "title": "A bibliometric overview of mRNA vaccine stability research from 2020 to 2025",
        "abstract": (
            "Bibliometric analysis reveals rapid growth in mRNA vaccine stability research, "
            "especially after 2021. Dominant themes include lipid nanoparticle optimization, "
            "cold-chain reduction, and lyophilization. Underexplored areas include cost "
            "optimization, large-scale comparative trials, and toxicity monitoring."
        ),
        "journal": "Frontiers in Immunology",
        "year": 2025,
        "doi": "10.3389/fimmu.2025.123456",
    },
    {
        "title": "Clinical considerations for next-generation RNA vaccine storage",
        "abstract": (
            "Clinical deployment of next-generation RNA vaccines requires balancing "
            "immunogenicity, formulation stability, and supply-chain feasibility. Current "
            "clinical evidence remains fragmented across disease areas and formulation types."
        ),
        "journal": "The Lancet Digital Health",
        "year": 2024,
        "doi": "10.1016/S2589-7500(24)00042-6",
    },
    {
        "title": "Large language models for evidence synthesis in biomedical policy teams",
        "abstract": (
            "Large language models can accelerate evidence synthesis for biomedical policy "
            "teams by drafting summaries and identifying recurring themes. Risks include "
            "hallucinated citations and insufficient traceability. Hybrid review workflows "
            "with source grounding are recommended."
        ),
        "journal": "NPJ Digital Medicine",
        "year": 2024,
        "doi": "10.1038/s41746-024-01011-2",
    },
]
