# college_data.py — IITJ Specific
# ══════════════════════════════════════════

COLLEGE_INFO = {
    "name": "Indian Institute of Technology Jodhpur",
    "short": "IITJ",
    "location": "Jodhpur, Rajasthan",
    "domain": "@iitj.ac.in"
}

# ══════════════════════════════════════════
# FESTS — IITJ
# ══════════════════════════════════════════
FESTS = {
    "IGNUS": {
        "full_name": "Ignus — Annual Socio-Cultural Fest",
        "type": "cultural",
        "keywords": ["ignus", "cultural", "dance", "music", "drama",
                     "art", "nukkad", "stage show", "band", "socio-cultural"],
        "held": "February",
        "emails": ["registration", "audition", "performance", "event", "pronite"]
    },
    "PROMETEO": {
        "full_name": "Prometeo — National Technical + Entrepreneurial Fest",
        "type": "technical",
        "keywords": ["prometeo", "tech fest", "technical", "entrepreneurial",
                     "startup", "innovation", "workshop", "competition"],
        "held": "January",
        "emails": ["registration", "workshop", "talk", "competition", "prize"]
    },
    "VARCHAS": {
        "full_name": "Varchas — Annual Sports Fest",
        "type": "sports",
        "keywords": ["varchas", "sports", "football", "cricket", "basketball",
                     "badminton", "athletics", "tennis", "volleyball"],
        "held": "February",
        "emails": ["registration", "team", "match", "event", "sports"]
    },
    "NIMBLE": {
        "full_name": "Nimble — Intra-College Science & Technology Fest",
        "type": "technical",
        "keywords": ["nimble", "robotics", "electronics", "programming",
                     "science", "technology", "quiz", "intra"],
        "emails": ["event", "registration", "competition", "robotics"]
    },
    "SPANDAN": {
        "full_name": "Spandan — Intra-College Cultural Fest",
        "type": "cultural",
        "keywords": ["spandan", "intra", "cultural", "performance"],
        "emails": ["event", "performance", "participate"]
    },
    "FRAMED": {
        "full_name": "Framed — Design & Arts Flagship Event",
        "type": "arts",
        "keywords": ["framed", "design", "art", "artwork", "gallery",
                     "canvas", "illustration", "creative"],
        "emails": ["submission", "exhibition", "gallery", "event"]
    },
    "VIRASAAT": {
        "full_name": "Virasaat — SPICMACAY Festival",
        "type": "cultural",
        "keywords": ["virasaat", "spicmacay", "classical", "heritage",
                     "traditional", "music", "culture"],
        "emails": ["performance", "event", "classical"]
    },
    "TECH_EXPO": {
        "full_name": "Tech Expo — Student Project Exhibition",
        "type": "technical",
        "keywords": ["tech expo", "project exhibition", "showcase",
                     "demo", "project", "exhibit"],
        "emails": ["submission", "registration", "demo", "project"]
    },
}

# ══════════════════════════════════════════
# CLUBS — IITJ (corrected names)
# ══════════════════════════════════════════
CLUBS = {
    "RAID": {
        "full_name": "RAID — Realm of Artificial Intelligence and Data",
        "type": "technical",
        "keywords": ["RAID", "AI", "artificial intelligence", "machine learning",
                     "data science", "deep learning", "ML", "neural networks",
                     "data", "LLM", "NLP", "computer vision"],
        "emails": ["webinar", "coding competition", "workshop", "talk", "session", "project"]
    },
    "ROBOTICS_CLUB": {
        "full_name": "Robotics Club IITJ",
        "type": "technical",
        "keywords": ["robotics club", "robotics", "embedded systems", "arduino",
                     "raspberry pi", "circuits", "automation", "hardware", "bot"],
        "emails": ["workshop", "competition", "tutorial", "project", "build"]
    },
    "DSC": {
        "full_name": "Developer Student Club (Google DSC)",
        "type": "technical",
        "keywords": ["DSC", "GDSC", "google", "android", "web development",
                     "flutter", "firebase", "cloud", "developer"],
        "emails": ["solution challenge", "devfest", "study jam", "workshop"]
    },
    "BOLTHEADS": {
        "full_name": "Boltheads — Automotive & Aerodynamics Club (SAE India)",
        "type": "technical",
        "keywords": ["boltheads", "SAE", "automotive", "aerodynamics", "vehicle",
                     "mechanical", "fabricate", "design", "formula", "car", "go-kart"],
        "emails": ["event", "competition", "design", "fabrication", "workshop"]
    },
    "ROTARACT": {
        "full_name": "Rotaract Club IITJ",
        "type": "social",
        "keywords": ["rotaract", "social", "volunteer", "community",
                     "service", "ngo", "help", "drive"],
        "emails": ["drive", "event", "volunteer", "activity", "meeting"]
    },
    "NEXUS": {
        "full_name": "Nexus — Astronomy Club",
        "type": "science",
        "keywords": ["nexus", "astronomy", "stars", "telescope",
                     "space", "cosmos", "stargazing", "astrophysics"],
        "emails": ["stargazing", "observation", "workshop", "session"]
    },
    "GROOVE_THEORY": {
        "full_name": "Groove Theory — Dance Club",
        "type": "cultural",
        "keywords": ["groove theory", "dance", "hip hop", "freestyle",
                     "contemporary", "choreography", "perform"],
        "emails": ["audition", "rehearsal", "performance", "workshop"]
    },
    "DRAMATICS": {
        "full_name": "Dramatics Club IITJ",
        "type": "cultural",
        "keywords": ["dramatics", "drama", "nukkad natak", "street play",
                     "mono acting", "mime", "skit", "theatre", "acting", "play"],
        "emails": ["audition", "rehearsal", "performance", "competition"]
    },
    "SHUTTERBUGS": {
        "full_name": "Shutterbugs — Photography Club",
        "type": "arts",
        "keywords": ["shutterbugs", "photography", "camera", "photo",
                     "shoot", "click", "portrait", "landscape"],
        "emails": ["photowalks", "workshop", "competition", "exhibition"]
    },
    "ATELIERS": {
        "full_name": "Ateliers — Art & Craft Club",
        "type": "arts",
        "keywords": ["ateliers", "art", "craft", "painting", "sketch",
                     "illustration", "creative", "drawing"],
        "emails": ["workshop", "exhibition", "session", "submission"]
    },

    # ── ACTIVE CLUBS (normal priority) ──

    "SANGAM": {
        "full_name": "Sangam — Music Society IITJ",
        "type": "cultural",
        "keywords": ["sangam", "music", "singing", "guitar", "drums",
                     "vocals", "band", "western music", "classical music",
                     "instruments", "jam", "concert", "acoustic"],
        "emails": ["audition", "jam session", "concert", "practice", "performance"]
    },
    "CHESS_SOCIETY": {
        "full_name": "Chess Society IITJ",
        "type": "sports",
        "keywords": ["chess society", "chess", "board games", "tournament",
                     "checkmate", "blitz", "rapid chess"],
        "emails": ["tournament", "session", "competition", "event"]
    },
    "QUANT_CLUB": {
        "full_name": "Quant Club IITJ",
        "type": "technical",
        "keywords": ["quant", "quant club", "quantitative", "finance",
                     "trading", "stocks", "mathematics", "statistics",
                     "probability", "financial modelling", "algo trading"],
        "emails": ["workshop", "talk", "competition", "session", "event"]
    },

    # ── SPORTS: umbrella council active, individual societies ignore until mentioned ──

    "SPORTS_COUNCIL": {
        "full_name": "Sports Council IITJ",
        "type": "sports",
        "keywords": ["sports council", "sports", "athletics", "varchas",
                     "inter iit", "sports meet", "sports day", "gym"],
        "emails": ["registration", "team", "tryout", "match", "event", "sports"]
    },

    # individual sports — ignore until user specifically mentions them
    "FOOTBALL_SOCIETY": {
        "full_name": "Football Society IITJ",
        "type": "sports",
        "default_priority": "ignore",
        "keywords": ["football", "soccer", "football society", "futsal"],
        "emails": ["match", "tryout", "practice", "tournament"]
    },
    "CRICKET_SOCIETY": {
        "full_name": "Cricket Society IITJ",
        "type": "sports",
        "default_priority": "ignore",
        "keywords": ["cricket", "cricket society", "net practice", "batting", "bowling"],
        "emails": ["match", "tryout", "practice", "tournament"]
    },
    "BASKETBALL_SOCIETY": {
        "full_name": "Basketball Society IITJ",
        "type": "sports",
        "default_priority": "ignore",
        "keywords": ["basketball", "basketball society", "hoops"],
        "emails": ["match", "tryout", "practice", "tournament"]
    },
    "TABLE_TENNIS_SOCIETY": {
        "full_name": "Table Tennis Society IITJ",
        "type": "sports",
        "default_priority": "ignore",
        "keywords": ["table tennis", "TT", "ping pong", "table tennis society"],
        "emails": ["match", "tryout", "practice", "tournament"]
    },
    "BADMINTON_SOCIETY": {
        "full_name": "Badminton Society IITJ",
        "type": "sports",
        "default_priority": "ignore",
        "keywords": ["badminton", "badminton society", "shuttlecock"],
        "emails": ["match", "tryout", "practice", "tournament"]
    },
}

# ══════════════════════════════════════════
# IITJ ACADEMIC TERMS
# ══════════════════════════════════════════
ACADEMIC = {
    "MST":         "Mid Semester Test — important exam",
    "EST":         "End Semester Test — most important exam",
    "CIA":         "Continuous Internal Assessment",
    "CPI":         "Cumulative Performance Index (GPA equivalent)",
    "HOD":         "Head of Department — always high priority",
    "viva":        "Oral exam — high priority",
    "lab record":  "Lab submission — deadline sensitive",
    "backlog":     "Failed subject to be cleared",
    "TA":          "Teaching Assistant",
    "SWC":         "Student Wellbeing Committee",
    "gymkhana":    "Student body governing all clubs and fests",
    "SAC":         "Student Activity Centre",
}

# ══════════════════════════════════════════
# TRUSTED SENDERS — always high priority
# ══════════════════════════════════════════
TRUSTED_SENDERS = [
    "@iitj.ac.in",
    "exam@iitj.ac.in",
    "fees@iitj.ac.in",
    "hostel@iitj.ac.in",
    "placement@iitj.ac.in",
    "swc@iitj.ac.in",
]

# ══════════════════════════════════════════
# INTEREST MAP — user text → club codes
# This is what makes "I like AI" → RAID
# ══════════════════════════════════════════
INTEREST_MAP = {
    "AI":                   ["RAID", "PROMETEO"],
    "artificial intelligence": ["RAID"],
    "machine learning":     ["RAID"],
    "data science":         ["RAID"],
    "deep learning":        ["RAID"],
    "coding":               ["RAID", "DSC"],
    "competitive programming": ["RAID", "DSC"],
    "web dev":              ["DSC"],
    "web development":      ["DSC"],
    "google":               ["DSC"],
    "android":              ["DSC"],
    "robotics":             ["ROBOTICS_CLUB", "NIMBLE"],
    "embedded":             ["ROBOTICS_CLUB"],
    "hardware":             ["ROBOTICS_CLUB", "BOLTHEADS"],
    "cars":                 ["BOLTHEADS"],
    "automotive":           ["BOLTHEADS"],
    "mechanical":           ["BOLTHEADS"],
    "dance":                ["GROOVE_THEORY", "IGNUS"],
    "drama":                ["DRAMATICS", "IGNUS"],
    "theatre":              ["DRAMATICS"],
    "acting":               ["DRAMATICS"],
    "photography":          ["SHUTTERBUGS", "FRAMED"],
    "art":                  ["ATELIERS", "FRAMED"],
    "craft":                ["ATELIERS"],
    "astronomy":            ["NEXUS"],
    "space":                ["NEXUS"],
    "stars":                ["NEXUS"],
    "social work":          ["ROTARACT"],
    "volunteer":            ["ROTARACT"],
    "sports":               ["SPORTS_COUNCIL", "VARCHAS"],

    # individual sports — only activate if user specifically says these
    "football":             ["FOOTBALL_SOCIETY"],
    "cricket":              ["CRICKET_SOCIETY"],
    "basketball":           ["BASKETBALL_SOCIETY"],
    "table tennis":         ["TABLE_TENNIS_SOCIETY"],
    "TT":                   ["TABLE_TENNIS_SOCIETY"],
    "badminton":            ["BADMINTON_SOCIETY"],
    "cultural":             ["IGNUS", "SPANDAN"],
    "technical":            ["PROMETEO", "NIMBLE"],
    "music":                ["IGNUS", "VIRASAAT"],
    "classical music":      ["VIRASAAT"],
    "design":               ["FRAMED", "ATELIERS"],
    "startup":              ["PROMETEO"],
    "entrepreneurship":     ["PROMETEO"],

    # ── only activate if user specifically says these ──
    "music":                ["SANGAM", "IGNUS", "VIRASAAT"],  # SANGAM now active
    "singing":              ["SANGAM"],
    "guitar":               ["SANGAM"],
    "band":                 ["SANGAM"],
    "chess":                ["CHESS_SOCIETY"],
    "board games":          ["CHESS_SOCIETY"],
    "quant":                ["QUANT_CLUB"],
    "finance":              ["QUANT_CLUB"],
    "trading":              ["QUANT_CLUB"],
    "statistics":           ["QUANT_CLUB"],
    "algo trading":         ["QUANT_CLUB"],
}
