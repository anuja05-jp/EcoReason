# EcoReason — AI Biodiversity Intelligence Chatbot

EcoReason is an AI environmental reasoning system built for the Darukaa.Earth assessment. It retrieves real environmental data for a location, detects environmental stress signals and multi-variable interactions, retrieves relevant scientific evidence using RAG, and generates evidence-backed recommendations through a conversational interface.

**Live Demo:** https://ecoreason-environmentalscientist.streamlit.app/

**Repository:** https://github.com/anuja05-jp/EcoReason

---

## Architecture

User Input
    |
    v
Geocoding
    |
    v
Environmental Profile
    |
    +-- SoilGrids
    +-- Open-Meteo
    +-- GBIF
    +-- ESA WorldCover
    +-- Global Forest Watch
    |
    v
Signal Detection
    |
    v
Multi-Variable Reasoning
    |
    v
RAG Evidence Retrieval
    |
    v
Gemini Reasoning
    |
    v
Code-Level Validation
    |
    v
Streamlit Conversational Interface

The system separates environmental data collection, deterministic reasoning, evidence retrieval, LLM generation, and output validation.

---

## Data Sources

| Category      | Source                 | Access          |
| ------------- | ---------------------- | --------------- |
| Soil          | ISRIC SoilGrids        | WCS             |
| Climate       | Open-Meteo             | REST API        |
| Air Quality   | Open-Meteo Air Quality | REST API        |
| Biodiversity  | GBIF                   | Occurrence API  |
| Land Cover    | ESA WorldCover         | Geospatial data |
| Land Use      | OpenStreetMap          | Overpass API    |
| Deforestation | Global Forest Watch    | Data API        |

Environmental variables include soil organic carbon, soil pH, moisture where available, temperature, precipitation, air quality, biodiversity, land-cover composition, habitat diversity, and tree-cover loss.

---

## Environmental Reasoning

EcoReason uses a rule-based reasoning layer to identify environmental signals such as:

* Soil carbon stress
* Rainfall stress
* Monoculture
* Built-up land dominance
* Habitat diversity
* Biodiversity diversity
* Tree-cover loss
* Air-quality pressure

Detected signals are combined into multi-variable interactions, allowing recommendations to consider multiple environmental conditions together rather than relying on a generic LLM response.

---

## RAG Pipeline

1. **Knowledge Base:** Environmental knowledge documents in `data/knowledge_text/` are embedded using `sentence-transformers/all-MiniLM-L6-v2`.

2. **Vector Storage:** Embeddings are stored in a persistent ChromaDB collection.

3. **Retrieval:** `rag_reasoning.py` retrieves relevant evidence for detected environmental interactions.

4. **Generation:** `gemini_reasoner.py` provides the environmental profile, detected interactions, and retrieved evidence to Gemini.

5. **Validation:** Generated recommendations are validated in code. Evidence sources must correspond to retrieved evidence, and recommendations are checked for multiple variables, impacted metrics, confidence, measurement guidance, and limitations.

---

## Database / Vector DB

**Vector database:** ChromaDB

**Location:** `data/vector_db/`

**Embedding model:** `sentence-transformers/all-MiniLM-L6-v2`

The vector database is generated from the knowledge documents. If the collection is empty, the application automatically builds it from `data/knowledge_text/`. This allows deployment without committing the generated vector database to GitHub.

Structured environmental and runtime data are stored as JSON under `data/structured/`.

---

## Environment Variables

Create a `.env` file in the project root:

GEMINI_API_KEY=your_gemini_api_key
GFW_API_KEY=your_global_forest_watch_api_key


API keys are not committed to GitHub. Streamlit Community Cloud uses its Secrets configuration for deployment.

---

## Local Setup

```bash
git clone https://github.com/anuja05-jp/EcoReason.git
cd EcoReason

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

python build_knowledge_base.py

streamlit run app.py
```

For macOS/Linux, activate the environment using:

```bash
source venv/bin/activate
```

---

## Deployment

EcoReason is deployed using Streamlit Community Cloud.

Repository: anuja05-jp/EcoReason
Branch: main
Entrypoint: app.py
Python: 3.12


**Live Demo:** [https://ecoreason-environmentalscientist.streamlit.app/](https://ecoreason-environmentalscientist.streamlit.app/)

Changes pushed to the `main` branch trigger application updates through Streamlit Community Cloud. No separate GitHub Actions workflow is currently configured.

---

## Example Input / Output

### Conversational Input

Location: Jaipur, India
Farming practice: monoculture wheat

The system retrieves environmental data for the location and combines it with the user's land-use information.

### Clarifying Input

For an insufficient input such as:

Biodiversity is declining on my land.

the system asks for additional context such as location and crop or land-use information before performing the analysis.

### Example Recommendation

Action:
Transition from monoculture toward crop diversification and cover cropping.

Why:
Addresses detected interactions between land-use practices,
soil conditions, and biodiversity.

Variables involved:
Monoculture, soil organic carbon, biodiversity.

Impacted metrics:
Taxonomic diversity, soil organic carbon, habitat diversity.

Time horizon:
Medium term.

How to measure:
Monitor biodiversity and soil indicators over time.

Evidence source:
Retrieved knowledge-base source.

Confidence:
High

### Structured JSON Input

```json
{
  "location_name": "Jaipur, India",
  "farmer_input": {
    "land_use": "monoculture wheat",
    "region": "semi-arid"
  }
}
```

---

## Project Structure

EcoReason/
├── app.py
├── gemini_reasoner.py
├── reasoning_engine.py
├── rag_reasoning.py
├── retrieve_knowledge.py
├── build_knowledge_base.py
├── structured_input.py
├── live_environment_profile.py
├── soilgrids.py
├── collect_biodiversity.py
├── collect_climate.py
├── collect_deforestation.py
├── data/
│   └── knowledge_text/
├── archive/
├── example_input.json
├── requirements.txt
└── README.md

---

## Limitations

* Environmental data availability varies by location.
* Different datasets have different spatial and temporal resolutions.
* SoilGrids may not return data for every location; the system widens its search area and preserves missing values when necessary.
* Global Forest Watch data availability varies by location and time period.
* Air-quality values represent the queried location and are not full pollution-source attribution models.
* Gemini API availability and rate limits depend on the configured model and usage tier.

Environmental recommendations are decision-support outputs and should be considered alongside local ecological knowledge and domain expertise.

---

## Security

API credentials are stored using environment variables and Streamlit Community Cloud Secrets.

`.env`, runtime-generated JSON files, and the generated vector database are excluded from version control where appropriate.

---

## Project Context

EcoReason was developed for the Darukaa.Earth assessment to demonstrate an environmental intelligence system combining real-world environmental data, multi-variable reasoning, Retrieval-Augmented Generation, evidence-grounded recommendations, conversational interaction, and generative AI.
