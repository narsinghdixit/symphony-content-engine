# Project Symphony

GTM Intelligence + Action Layer for PureFacts Financial Solutions.

A two-phase AI system: strategy agents debate the best campaign play for a source document, you approve the brief, and the engine generates and distributes a full marketing campaign kit (LinkedIn posts, nurture emails, BDR sequences, blog post, sales one-pager, and more) -- pushed live to LinkedIn, HubSpot, and Gmail with one click each.

## Architecture

```
Upload Source Document
        |
        v
Phase 1: Intelligence
  - Agent A (ToFu Brand Strategist)  ---debate--->  Agent B (BoFu Pipeline Strategist)
        |                                                       |
        +----------------> Synthesizer Agent <------------------+
                                  |
                                  v
                          Campaign Brief
                                  |
                +-----------------+-----------------+
                |                                   |
          Email to You                       Brief in App
                                  |
                                  v
                       Approval Gate (You)
                                  |
                                  v
Phase 2: Execution (Gemini)
  10 marketing assets generated, informed by approved strategy
                                  |
                                  v
Phase 3: Distribution
  LinkedIn (copy + open) | HubSpot (push drafts) | Gmail (send for approval)
```

## Two Ways to Run

### 1. Streamlit Web App (`app.py`)

For Narsingh and the marketing team. Live URL, drag-and-drop, click-through workflow with integrations.

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml  # then fill in real keys
streamlit run app.py
```

### 2. Cursor Agent Mode (`AGENTS.md`)

For power users. Type `symphony, compose magic` in a Cursor Agent Mode chat to run the full pipeline against documents in `/inbox/`.

## Project Structure

```
symphony-content-engine/
|-- app.py                    Streamlit app
|-- ingest.py                 Convert .docx and .pdf to markdown
|-- AGENTS.md                 Cursor Agent Mode orchestration
|-- README.md                 You are here
|-- requirements.txt
|-- .gitignore
|-- .streamlit/
|   |-- config.toml           Theme
|   `-- secrets.toml.example  Template for API keys
|-- context/                  THE MOAT: PureFacts positioning, ICP, voice
|   |-- company.md
|   |-- icp.md
|   |-- positioning.md
|   |-- competitors.md
|   `-- brand-voice.md
|-- prompts/                  System prompts for each agent
|   |-- 01-extract.md
|   |-- 02-multiply.md
|   |-- 03-debate.md
|   `-- 04-synthesize.md
|-- tests/                    Integration smoke tests
|   |-- test_linkedin.py
|   |-- test_gmail.py
|   `-- test_hubspot.py
|-- inbox/                    Source documents (gitignored)
`-- output/                   Generated assets (gitignored)
```

## Tech Stack

- **LLM**: Google Gemini (2.0 Flash for speed, 1.5 Pro for synthesis)
- **App**: Streamlit
- **Integrations**: HubSpot Marketing Email API, Gmail SMTP, LinkedIn share URLs
- **Deployment**: Streamlit Community Cloud
- **Language**: Python 3.10+

## Status

V2 in active development. Targeting President demo and PureFacts Townhall.
