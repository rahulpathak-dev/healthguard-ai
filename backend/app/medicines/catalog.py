from dataclasses import dataclass


@dataclass(frozen=True)
class MedicineMonograph:
    generic_name: str
    brand_names: tuple[str, ...]
    common_uses: tuple[str, ...]
    common_side_effects: tuple[str, ...]
    serious_warnings: tuple[str, ...]
    precautions: tuple[str, ...]
    interactions: tuple[str, ...]
    storage_information: tuple[str, ...]
    pregnancy_child_elderly_cautions: tuple[str, ...]
    references: tuple[tuple[str, str, str, str], ...]


CATALOG: tuple[MedicineMonograph, ...] = (
    MedicineMonograph(
        generic_name="acetaminophen",
        brand_names=("Tylenol",),
        common_uses=("Pain relief", "Fever reduction"),
        common_side_effects=("Nausea or stomach upset may occur in some people.",),
        serious_warnings=(
            "Too much acetaminophen can cause serious liver injury.",
            "Avoid combining products that both contain acetaminophen unless a clinician or "
            "pharmacist confirms it is safe.",
        ),
        precautions=(
            "Ask a clinician or pharmacist before use with liver disease or heavy alcohol use.",
            "Check labels because many cough, cold, and combination products may contain "
            "acetaminophen.",
        ),
        interactions=("Warfarin and other medicines may require clinician or pharmacist review.",),
        storage_information=("Store at room temperature away from excess heat and moisture.",),
        pregnancy_child_elderly_cautions=(
            "Pregnancy, children, older adults, and people with liver disease should use "
            "clinician or pharmacist guidance.",
        ),
        references=(
            (
                "Acetaminophen",
                "MedlinePlus",
                "https://medlineplus.gov/druginfo/meds/a681004.html",
                "Consumer drug information from the U.S. National Library of Medicine.",
            ),
        ),
    ),
    MedicineMonograph(
        generic_name="ibuprofen",
        brand_names=("Advil", "Motrin"),
        common_uses=("Pain relief", "Fever reduction", "Inflammation-related pain relief"),
        common_side_effects=("Upset stomach, nausea, heartburn, or dizziness can occur.",),
        serious_warnings=(
            "Nonsteroidal anti-inflammatory drugs can increase risk of serious heart, "
            "stomach, or bleeding problems in some people.",
        ),
        precautions=(
            "Ask a clinician or pharmacist before use with ulcers, kidney disease, heart "
            "disease, blood thinners, or other NSAIDs.",
        ),
        interactions=(
            "Blood thinners, aspirin, certain blood pressure medicines, lithium, "
            "methotrexate, and other NSAIDs may require review.",
        ),
        storage_information=("Store at room temperature away from excess heat and moisture.",),
        pregnancy_child_elderly_cautions=(
            "Avoid late-pregnancy use unless specifically directed by a clinician.",
            "Children and older adults need extra caution and product-specific guidance.",
        ),
        references=(
            (
                "Ibuprofen",
                "MedlinePlus",
                "https://medlineplus.gov/druginfo/meds/a682159.html",
                "Consumer drug information from the U.S. National Library of Medicine.",
            ),
        ),
    ),
    MedicineMonograph(
        generic_name="amoxicillin",
        brand_names=("Amoxil",),
        common_uses=("Treatment of certain bacterial infections when prescribed by a clinician.",),
        common_side_effects=("Nausea, vomiting, diarrhea, or rash may occur.",),
        serious_warnings=(
            "Serious allergic reactions can occur and need urgent care.",
            "Antibiotics should not be used for viral infections unless a clinician "
            "determines a bacterial infection is present.",
        ),
        precautions=(
            "Tell a clinician about penicillin or cephalosporin allergy history.",
            "Use only as prescribed and ask about missed-dose instructions from a pharmacist.",
        ),
        interactions=(
            "Some blood thinners and other medicines may require clinician or pharmacist review.",
        ),
        storage_information=(
            "Follow the pharmacy label; some liquid forms may require refrigeration.",
        ),
        pregnancy_child_elderly_cautions=(
            "Pregnancy, children, and older adults should use individualized clinician guidance.",
        ),
        references=(
            (
                "Amoxicillin",
                "MedlinePlus",
                "https://medlineplus.gov/druginfo/meds/a685001.html",
                "Consumer drug information from the U.S. National Library of Medicine.",
            ),
        ),
    ),
    MedicineMonograph(
        generic_name="metformin",
        brand_names=("Glucophage", "Fortamet", "Glumetza"),
        common_uses=("Blood sugar management in type 2 diabetes when prescribed by a clinician.",),
        common_side_effects=("Diarrhea, nausea, gas, weakness, or stomach discomfort can occur.",),
        serious_warnings=(
            "Rare lactic acidosis can be serious and needs urgent medical attention.",
        ),
        precautions=(
            "Kidney function, liver disease, alcohol use, imaging contrast, and surgery "
            "plans may require clinician review.",
        ),
        interactions=(
            "Some medicines and contrast dyes may require temporary care-plan changes by "
            "a clinician.",
        ),
        storage_information=("Store at room temperature away from excess heat and moisture.",),
        pregnancy_child_elderly_cautions=(
            "Pregnancy, children, and older adults need individualized clinician guidance.",
            "Kidney function is especially important in older adults.",
        ),
        references=(
            (
                "Metformin",
                "MedlinePlus",
                "https://medlineplus.gov/druginfo/meds/a696005.html",
                "Consumer drug information from the U.S. National Library of Medicine.",
            ),
        ),
    ),
)

ALIASES = {item.generic_name: item for item in CATALOG}
for item in CATALOG:
    for brand in item.brand_names:
        ALIASES[brand.lower()] = item
