"""
APSIT AI — Callup Questions
-----------------------------
Instant answers for ultra-common questions.
Bypasses Qdrant + Gemini → zero cost, zero latency.

HOW TO ADD:
  Append a dict to CALLUP_QA with:
    keywords: list[str]  — any word triggers this entry
    answer:   str        — response text
    images:   list[str]  — image URLs (optional)
    pdfs:     list[str]  — PDF URLs (optional)
    videos:   list[str]  — YouTube URLs (optional)
    links:    list[dict] — [{label, url}] redirect buttons (optional)
"""

from typing import Optional

CALLUP_QA = [

    # ── FEES / PAYMENT ────────────────────────────────────────
    {
        "keywords": ["fee", "fees", "tuition", "payment", "pay", "cost",
                     "charges", "फी", "शुल्क", "challan"],
        "answer": (
            "Here are the APSIT fee details. "
            "You can preview or download the official fee structure below.\n\n"
            "For online payment, please use the APSIT Payment Portal."
        ),
        "images": [
            "https://www.apsit.edu.in/images/fees/fees_structure.jpg",
        ],
        "pdfs": [
            "https://www.apsit.edu.in/pdf/fee_structure.pdf",
        ],
        "videos": [],
        "links": [
            {"label": "💳 Pay Fees Online", "url": "https://admission.apsit.org.in/"},
        ],
    },

    # ── ADMISSION ─────────────────────────────────────────────
    {
        "keywords": ["admission", "apply", "application", "enroll",
                     "enrollment", "register", "registration", "प्रवेश"],
        "answer": (
            "For admissions and all payment-related queries, "
            "visit the official APSIT Admission Portal."
        ),
        "images": [],
        "pdfs":   [],
        "videos": [],
        "links": [
            {"label": "🎓 APSIT Admission Portal", "url": "https://admission.apsit.org.in/"},
        ],
    },

    # ── ACHIEVEMENTS ─────────────────────────────────────────
    {
        "keywords": ["achievement", "achievements", "award", "awards",
                     "won", "prize", "rank", "accomplishment", "milestone"],
        "answer": (
            "APSIT has achieved many milestones! "
            "Below are some highlights including videos and the institute brochure."
        ),
        "images": [],
        "pdfs": [
            "https://www.apsit.edu.in/pdf/institute_brochure.pdf",
        ],
        "videos": [
            "https://www.youtube.com/@APSITOfficial",
        ],
        "links": [
            {"label": "📖 View Brochure",    "url": "https://www.apsit.edu.in/pdf/institute_brochure.pdf"},
            {"label": "🏆 Achievements Page", "url": "https://www.apsit.edu.in/achievements"},
        ],
    },

    # ── BROCHURE ─────────────────────────────────────────────
    {
        "keywords": ["brochure", "prospectus", "catalogue", "booklet"],
        "answer": "Here is the official APSIT Institute Brochure. Preview or download it below:",
        "images": [],
        "pdfs": [
            "https://www.apsit.edu.in/pdf/institute_brochure.pdf",
        ],
        "videos": [],
        "links": [
            {"label": "📥 Download Brochure", "url": "https://www.apsit.edu.in/pdf/institute_brochure.pdf"},
        ],
    },

    # ── MOODLE / ANNOUNCEMENTS ────────────────────────────────
    {
        "keywords": ["moodle", "elearn", "e-learn", "lms", "announcement",
                     "notice", "circular", "notification"],
        "answer": (
            "APSIT's e-learning portal (Moodle) has important announcements, "
            "study materials, and lecture notes. Check it regularly!"
        ),
        "images": [],
        "pdfs":   [],
        "videos": [],
        "links": [
            {"label": "📚 Open Moodle Portal", "url": "https://elearn.apsit.edu.in/moodle/"},
        ],
    },

    # ── PLACEMENTS ───────────────────────────────────────────
    {
        "keywords": ["placement", "placements", "job", "jobs", "campus",
                     "recruit", "company", "package", "salary", "career", "hiring"],
        "answer": (
            "APSIT has an excellent placement record with top companies visiting every year. "
            "Visit the placements page for company names, packages, and student testimonials."
        ),
        "images": [],
        "pdfs":   [],
        "videos": [],
        "links": [
            {"label": "💼 Placements Page", "url": "https://www.apsit.edu.in/placements"},
        ],
    },

    # ── CONTACT ──────────────────────────────────────────────
    {
        "keywords": ["contact", "phone", "email", "address", "location",
                     "office", "helpline", "reach", "संपर्क"],
        "answer": (
            "You can reach APSIT at:\n"
            "📍 A-45, Road No.1, MIDC, Andheri East, Mumbai - 400 093\n"
            "📞 +91-22-2895 5500\n"
            "🌐 www.apsit.edu.in"
        ),
        "images": [],
        "pdfs":   [],
        "videos": [],
        "links": [
            {"label": "🌐 Visit Website", "url": "https://www.apsit.edu.in/contact"},
        ],
    },

]


def match_callup(query: str) -> Optional[dict]:
    """
    Returns the first matching callup entry or None.
    Matching is keyword-based on lowercased query.
    """
    q_lower = query.lower()
    for entry in CALLUP_QA:
        if any(kw in q_lower for kw in entry["keywords"]):
            return entry
    return None
