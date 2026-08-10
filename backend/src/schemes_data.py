"""
Local database of government schemes and their eligibility criteria.
Note: This is a local approximate dataset for demonstration purposes, 
not a live government API. Final eligibility should always be verified 
at an official bank or government portal.
"""

SCHEMES = {
    "pm_vaya_vandana_yojana": {
        "name": "PM Vaya Vandana Yojana",
        "criteria": {
            "min_age": 60,
        },
        "benefit_summary": "Pension scheme for senior citizens offering a guaranteed payout.",
        "data_as_of": "2025 official guidelines (approximate local dataset)"
    },
    "pm_fasal_bima_yojana": {
        "name": "PM Fasal Bima Yojana",
        "criteria": {
            "is_farmer": True,
        },
        "benefit_summary": "Crop insurance scheme protecting farmers against crop failure.",
        "data_as_of": "2025 official guidelines (approximate local dataset)"
    },
    "pm_awas_yojana": {
        "name": "PM Awas Yojana",
        "criteria": {
            "max_annual_income": 1800000, 
            "must_not_own_pucca_house": True,
        },
        "benefit_summary": "Subsidized home loan scheme for affordable housing.",
        "data_as_of": "2025 official guidelines (approximate local dataset)"
    },
    "pm_ujjwala_yojana": {
        "name": "PM Ujjwala Yojana",
        "criteria": {
            "is_bpl_or_poor": True,
            "has_existing_lpg_connection": False,
            "applicant_is_female": True,
        },
        "benefit_summary": "Provides free LPG connections to women from below poverty line (BPL) households.",
        "data_as_of": "2025 official guidelines (approximate local dataset)"
    },
    "national_pension_system": {
        "name": "National Pension System",
        "criteria": {
            "min_age": 18,
            "max_age": 70,
            "is_indian_citizen": True,
        },
        "benefit_summary": "Voluntary, long-term retirement savings scheme.",
        "data_as_of": "2025 official guidelines (approximate local dataset)"
    },
    "pm_suraksha_bima_yojana": {
        "name": "Pradhan Mantri Suraksha Bima Yojana",
        "criteria": {
            "min_age": 18,
            "max_age": 70,
            "has_bank_account": True,
        },
        "benefit_summary": "Accident insurance scheme offering accidental death and disability cover.",
        "data_as_of": "2025 official guidelines (approximate local dataset)"
    }
}
