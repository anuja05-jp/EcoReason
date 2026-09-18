import os

KNOWLEDGE_DIR = "data/knowledge_text"
os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

documents = {

"cover_crops.txt": """
Topic: Cover crops and soil-water-biodiversity relationships

Cover crops maintain living or residual vegetation on agricultural soil between or alongside commercial crops. FAO identifies soil cover as a fundamental principle of conservation agriculture. Cover crops can protect soil during fallow periods, recycle nutrients, add organic matter, improve soil structure and help break compacted layers.

Cover crops can also influence water dynamics. Vegetative cover protects soil from raindrop impact, reduces evaporation and can increase infiltration. Different rooting systems explore different soil depths and can contribute to nutrient cycling and soil biological activity.

The biodiversity effect is also relevant: introducing additional plant species into a monoculture increases plant diversity within the agroecosystem and can provide resources for organisms associated with agricultural landscapes.

Reasoning connection:
Low soil organic carbon + low rainfall + monoculture can indicate a need to improve soil cover and water retention. Cover crops may simultaneously affect soil carbon, moisture retention, nutrient cycling and agroecosystem biodiversity.

Source: FAO Conservation Agriculture — Soil Organic Cover
https://www.fao.org/conservation-agriculture/in-practice/soil-organic-cover/en/
""",

"conservation_agriculture.txt": """
Topic: Conservation agriculture

FAO defines conservation agriculture around three principles: minimum mechanical soil disturbance, permanent soil organic cover and diversification of plant species. These principles are intended to support biological processes above and below the soil surface.

Maintaining soil cover protects soil from erosion and helps conserve moisture. Reduced disturbance can protect soil structure and biological activity. Plant diversification can increase biological diversity and improve the use of water and nutrients.

These practices are particularly relevant when environmental data indicate degraded soil conditions, erosion risk, low organic carbon or water stress.

Reasoning connection:
If soil organic carbon is low and rainfall is limited, maintaining soil cover and reducing soil disturbance can address multiple interacting soil-water processes rather than treating carbon as an isolated variable.

Source: FAO Conservation Agriculture
https://www.fao.org/conservation-agriculture/
""",

"agroforestry.txt": """
Topic: Agroforestry and ecosystem functions

Agroforestry integrates trees or shrubs with crops and/or livestock. FAO identifies environmental benefits including improved soil health and water management, reduced soil and wind erosion, improved microclimates, restoration of degraded land and enhanced farm biodiversity.

IPCC assessment also identifies agroforestry as a land-management option that can store carbon in woody vegetation and soil. Reported co-benefits include reduced soil erosion, improved water quality, improved soil infiltration and structural stability, reduced temperatures and crop heat stress, and potentially increased groundwater recharge in some dryland contexts.

However, agroforestry is context-dependent. Trees can compete with crops for water and resources, and inappropriate designs can create trade-offs with food production, biodiversity or local hydrology.

Reasoning connection:
Agroforestry can be considered when low soil carbon, erosion, heat stress or habitat fragmentation occur together, but the recommendation should account for rainfall, available water and local land-use conditions.

Sources:
FAO Agroforestry FAQs
https://www.fao.org/agroforestry/about-agroforestry/faqs/

IPCC AR6 WGIII Chapter 7
https://www.ipcc.ch/report/ar6/wg3/chapter/chapter-7/
""",

"crop_diversification.txt": """
Topic: Crop diversification

Crop diversification means increasing the variety of crops or plant species used across a farming system through rotations, mixtures or other forms of diversification. FAO includes species diversification as one of the three core principles of conservation agriculture.

Diversification can support biodiversity and biological processes in agricultural systems. Different plants have different rooting depths, nutrient requirements and interactions with soil organisms. This can influence nutrient cycling, soil structure and resource use.

IPCC identifies crop rotation, cover crops, perennial cropping systems and crop diversification among practices associated with increasing soil organic matter in croplands.

Reasoning connection:
When biodiversity indicators are low and land use is dominated by a single crop, diversification can be considered as an intervention that potentially addresses both biodiversity and soil-function dimensions.

The appropriate crop combination depends on local climate, soil conditions, water availability and farming objectives.

Sources:
FAO Conservation Agriculture
https://www.fao.org/conservation-agriculture/

IPCC AR6 WGIII Chapter 7
https://www.ipcc.ch/report/ar6/wg3/chapter/chapter-7/
""",

"soil_organic_carbon.txt": """
Topic: Soil organic carbon and ecosystem resilience

Soil organic carbon is an important component of soil organic matter and is connected to soil structure, nutrient cycling and water-related properties.

FAO identifies practices such as minimum tillage, crop rotation, organic matter addition and cover cropping as sustainable soil and water management practices that can improve soil health, reduce erosion and enhance water infiltration and storage.

IPCC identifies soil carbon management practices including crop rotation, cover crops, reduced tillage, residue retention, improved water management, organic amendments and agroforestry.

Soil carbon should not be interpreted in isolation. Its ecological significance depends on other environmental conditions such as rainfall, temperature, soil properties, land use and vegetation.

Reasoning connection:
Low soil organic carbon combined with low rainfall can indicate a stronger need to consider soil-cover and water-retention interventions than low carbon alone.

Sources:
FAO — Integrated soil and water management
https://www.fao.org/india/news/detail/Integrated-soil-and-water-management-essential-to-achieve-food-security-in-India-FAO/en

IPCC AR6 WGIII Chapter 7
https://www.ipcc.ch/report/ar6/wg3/chapter/chapter-7/
""",

"water_management.txt": """
Topic: Soil water management and ecosystem resilience

Water availability interacts strongly with soil condition, vegetation and climate. Soil cover can reduce evaporation and improve infiltration, while soil structure influences how water moves into and through the soil.

FAO describes soil cover as important for maintaining moisture and improving infiltration. Integrated soil and water management practices can improve water infiltration and storage and reduce erosion.

IPCC identifies improved water management as one component of soil-carbon and agricultural management. It also notes that some water-saving or land-based interventions can create trade-offs for rivers, wetlands or biodiversity depending on how they are implemented.

Reasoning connection:
When rainfall is low and soil organic carbon or vegetation cover is also low, recommendations should consider water retention and infiltration together with soil management.

Water interventions should be evaluated against local hydrology rather than assuming that increasing water use or irrigation is always beneficial.

Sources:
FAO — Soil Organic Cover
https://www.fao.org/conservation-agriculture/in-practice/soil-organic-cover/en/

IPCC AR6 WGIII Chapter 17
https://www.ipcc.ch/report/ar6/wg3/chapter/chapter-17/
""",

"habitat_connectivity.txt": """
Topic: Habitat connectivity and biodiversity

Biodiversity is influenced by land-use patterns as well as the condition of individual habitats. Fragmentation can separate habitat patches and reduce ecological connectivity.

Agroforestry and diversified agricultural landscapes can provide additional vegetation structure within working landscapes. FAO describes agroforestry as contributing to biodiversity conservation, while IPCC identifies biodiversity management and ecosystem connectivity as important land-system adaptation options.

Connectivity interventions should prioritize appropriate native or locally suitable vegetation and should not automatically replace existing natural ecosystems with plantations.

Reasoning connection:
If biodiversity richness is low and land-use information indicates fragmentation or intensive monoculture, improving habitat connectivity can complement on-farm biodiversity measures.

The recommendation should consider the surrounding landscape rather than evaluating a single field in isolation.

Sources:
FAO Agroforestry
https://www.fao.org/agroforestry/about-agroforestry/faqs/

IPCC AR6 Synthesis Report — Figure 4.5
https://www.ipcc.ch/report/ar6/syr/figures/figure-4-5/
""",

"nutrient_pollution.txt": """
Topic: Agricultural nutrient management and pollution

Agricultural nutrient management affects both production and environmental quality. Excess nutrient application can contribute to nutrient losses and environmental pollution.

FAO describes cover crops as useful for recycling nutrients and capturing nutrients that might otherwise be lost from the soil. Soil cover can therefore contribute to nutrient retention while also providing soil and water benefits.

IPCC identifies nutrient management as an agricultural management option and notes that some soil-carbon strategies can create trade-offs if they rely on additional fertilizer inputs, including potential increases in nitrous oxide emissions.

Reasoning connection:
When an environmental profile indicates intensive agriculture together with a pollution concern, the system should consider nutrient-management practices rather than recommending additional fertilizer simply because soil productivity is low.

Recommendations should consider soil conditions, crop requirements, rainfall and existing management.

Sources:
FAO — Soil Organic Cover
https://www.fao.org/conservation-agriculture/in-practice/soil-organic-cover/en/

IPCC AR6 WGIII Chapter 7
https://www.ipcc.ch/report/ar6/wg3/chapter/chapter-7/
""",

"land_use_biodiversity.txt": """
Topic: Land-use change, biodiversity and ecosystem protection

Land-use change can affect biodiversity, carbon storage, water systems and ecosystem functioning simultaneously. IPCC identifies protection, improved management and restoration of forests and other natural ecosystems as important land-based options.

Land-based interventions can generate multiple benefits, but IPCC emphasizes that poorly designed interventions can create trade-offs involving biodiversity, water, food production and livelihoods.

This means environmental recommendations should distinguish between restoring degraded land and converting intact natural ecosystems into managed plantations or other land uses.

Reasoning connection:
When biodiversity indicators are low and land-use pressure or deforestation risk is high, ecosystem protection and restoration may address biodiversity and carbon concerns simultaneously. The appropriate intervention depends on the existing ecosystem and surrounding land-use pattern.

Source: IPCC AR6 WGIII Chapter 7
https://www.ipcc.ch/report/ar6/wg3/chapter/chapter-7/
""",

"climate_biodiversity.txt": """
Topic: Climate conditions and biodiversity risk

Climate variables such as temperature and rainfall interact with soil, vegetation and habitat conditions. Biodiversity responses therefore should not be inferred from temperature or rainfall alone.

IPCC describes land-based adaptation options including agroforestry, biodiversity management, ecosystem connectivity, improved cropland management and water-resource management. The benefits and trade-offs of these options vary with location and scale.

A biodiversity recommendation should therefore combine climate information with land use, soil condition and biodiversity observations whenever possible.

Reasoning connection:
Low rainfall combined with low soil organic carbon and intensive land use represents a different ecological situation from low rainfall occurring in a well-vegetated natural ecosystem. The same intervention should not automatically be recommended for both.

EcoReason should use multiple environmental variables to identify interacting pressures before producing an intervention.

Source: IPCC AR6 WGII Chapter 18
https://www.ipcc.ch/report/ar6/wg2/chapter/chapter-18/
"""
}

for filename, content in documents.items():
    path = os.path.join(KNOWLEDGE_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())

print(f"Created {len(documents)} knowledge documents.")
print(f"Location: {KNOWLEDGE_DIR}")