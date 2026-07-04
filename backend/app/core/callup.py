"""
APSIT AI — Portal Shortcuts

Only keeps instant redirects for actions that should always open
an official APSIT portal.

Everything else is answered through:
Qdrant → Gemini
"""

from typing import Optional

CALLUP_QA = [

    # --------------------------------------------------------
    # FEES / PAYMENT
    # --------------------------------------------------------
    {
        "keywords": [
            "fee",
            "fees",
            "payment",
            "pay",
            "challan",
            "receipt",
            "tuition",
            "cost",
            "charges",
            "फी",
            "शुल्क"
        ],
        "answer": (
            "For fee payment, receipts and fee-related services, "
            "please use the official APSIT Online Payment Portal."
        ),
        "images": [],
        "pdfs": [],
        "videos": [],
        "links": [
            {
                "label": "💳 APSIT Payment Portal",
                "url": "https://admission.apsit.org.in/"
            }
        ]
    },

    # --------------------------------------------------------
    # ADMISSION
    # --------------------------------------------------------
    {
        "keywords": [
            "admission",
            "apply",
            "application",
            "register",
            "registration",
            "enroll",
            "enrollment",
            "प्रवेश"
        ],
        "answer": (
            "For admissions, applications and admission status, "
            "please visit the official APSIT Admission Portal."
        ),
        "images": [],
        "pdfs": [],
        "videos": [],
        "links": [
            {
                "label": "🎓 APSIT Admission Portal",
                "url": "https://admission.apsit.org.in/"
            }
        ]
    },

    # --------------------------------------------------------
    # MOODLE
    # --------------------------------------------------------
    {
        "keywords": [
            "moodle",
            "elearn",
            "e-learn",
            "lms"
        ],
        "answer": (
            "You can access APSIT's Moodle platform using the official portal below."
        ),
        "images": [],
        "pdfs": [],
        "videos": [],
        "links": [
            {
                "label": "📚 APSIT Moodle",
                "url": "https://elearn.apsit.edu.in/moodle/"
            }
        ]
    }

]


def match_callup(query: str) -> Optional[dict]:
    """
    Returns a portal shortcut if the query matches.

    All other questions continue through:
    Retriever → Gemini
    """

    q = query.lower().strip()

    for item in CALLUP_QA:
        if any(keyword in q for keyword in item["keywords"]):
            return item

    return None