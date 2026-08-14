import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("skillforge.resume_extractor")

# This vocabulary is deliberately conservative: it recognises technologies and
# well-known skill phrases, but never treats arbitrary prose as a skill.  It is
# used as a deterministic safety net when the NER model is unavailable.
SKILL_VOCABULARY = {
    "Python": ("python", "python 3", "python3"),
    "Java": ("java",),
    "JavaScript": ("javascript", "js", "ecmascript"),
    "TypeScript": ("typescript", "ts"),
    "C++": ("c++", "cpp"), "C#": ("c#", "c sharp"), "Kotlin": ("kotlin",),
    "React Native": ("react native",), "React": ("react", "reactjs", "react.js"),
    "Flask": ("flask",), "FastAPI": ("fastapi", "fast api"), "Django": ("django",),
    "Node.js": ("node.js", "nodejs", "node js"), "Express": ("express", "express.js", "expressjs"),
    "MongoDB": ("mongodb", "mongo db", "mongo"), "MySQL": ("mysql", "my sql"),
    "PostgreSQL": ("postgresql", "postgres", "postgre sql"), "SQL": ("sql",),
    "TensorFlow": ("tensorflow", "tensor flow", "tf"), "PyTorch": ("pytorch", "py torch", "torch"),
    "Keras": ("keras",), "scikit-learn": ("scikit-learn", "scikit learn", "sklearn"),
    "OpenCV": ("opencv", "open cv"), "CNN": ("cnn", "convolutional neural network"),
    "NLP": ("nlp", "natural language processing"), "Machine Learning": ("machine learning",),
    "Deep Learning": ("deep learning",), "Docker": ("docker",), "Git": ("git",),
    "GitHub": ("github",), "AWS": ("aws", "amazon web services"), "Azure": ("azure",),
    "GCP": ("gcp", "google cloud", "google cloud platform"), "Figma": ("figma",),
    "HTML": ("html",), "CSS": ("css",), "Tailwind": ("tailwind", "tailwind css", "tailwindcss"),
    "REST API": ("rest api", "restful api", "restful apis"), "OAuth": ("oauth",),
    "Google OAuth": ("google oauth",), "Firebase": ("firebase",),
}


def normalize_skills(skills: List[Any]) -> List[str]:
    """Return canonical, stable, duplicate-free skill names from known values."""
    aliases = {
        alias.casefold(): canonical
        for canonical, variants in SKILL_VOCABULARY.items()
        for alias in variants
    }
    result: List[str] = []
    seen = set()
    for value in skills:
        if not isinstance(value, str) or not value.strip():
            continue
        cleaned = value.strip()
        canonical = aliases.get(cleaned.casefold(), cleaned)
        key = canonical.casefold()
        if key not in seen:
            seen.add(key)
            result.append(canonical)
    return result


def extract_controlled_skills(raw_text: str) -> List[str]:
    """Find only controlled vocabulary entries anywhere in resume evidence."""
    found: List[tuple[int, int, str]] = []
    for canonical, variants in SKILL_VOCABULARY.items():
        positions = []
        for variant in variants:
            match = re.search(rf"(?<![\w+#]){re.escape(variant)}(?![\w+#])", raw_text, re.IGNORECASE)
            if match:
                positions.append((match.start(), match.end()))
        if positions:
            start, end = min(positions)
            found.append((start, end, canonical))
    # Prefer the longest match at a position and reject overlapping aliases:
    # "React Native" must never also emit "React", and Google OAuth should
    # not be duplicated as generic OAuth from the same evidence.
    result: List[str] = []
    occupied_until = -1
    for start, end, skill in sorted(found, key=lambda item: (item[0], -(item[1] - item[0]))):
        if start >= occupied_until:
            result.append(skill)
            occupied_until = end
    return result


def extract_academic_scores(text: str) -> Dict[str, Optional[float]]:
    """Deterministic parser for academic scores (SGPA, CGPA, GPA)."""
    scores: Dict[str, Optional[float]] = {"sgpa": None, "cgpa": None}

    # Match SGPA
    sgpa_match = re.search(r"(?i)\bSGPA\b\s*[:\-\=]?\s*([0-9]\.[0-9]{1,2}|10\.0|10)", text)
    if sgpa_match:
        try:
            scores["sgpa"] = float(sgpa_match.group(1))
        except ValueError:
            pass

    # Match CGPA
    cgpa_match = re.search(r"(?i)\bCGPA\b\s*[:\-\=]?\s*([0-9]\.[0-9]{1,2}|10\.0|10)", text)
    if cgpa_match:
        try:
            scores["cgpa"] = float(cgpa_match.group(1))
        except ValueError:
            pass

    # Fallback to general GPA if CGPA was not found
    if scores["cgpa"] is None:
        gpa_match = re.search(r"(?i)\bGPA\b\s*[:\-\=]?\s*([0-9]\.[0-9]{1,2}|4\.0|10\.0)", text)
        if gpa_match:
            try:
                scores["cgpa"] = float(gpa_match.group(1))
            except ValueError:
                pass

    return scores


def extract_dates_from_text(text: str) -> Dict[str, Optional[str]]:
    """Extract start date, end date, or year range from line/section text."""
    # Match years like 2022 - 2026 or 2022-2026
    year_range_match = re.search(r"\b(19\d\d|20\d\d)\s*[\-\–\—\to]+\s*(19\d\d|20\d\d|Present|Current|Now)\b", text, re.IGNORECASE)
    if year_range_match:
        return {
            "startDate": year_range_match.group(1),
            "endDate": year_range_match.group(2)
        }

    # Match Month Year - Month Year (e.g. May 2025 - July 2025)
    month_range_match = re.search(
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(19\d\d|20\d\d)\s*[\-\–\—\to]+\s*"
        r"(Present|Current|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(?:19\d\d|20\d\d))\b",
        text, re.IGNORECASE
    )
    if month_range_match:
        return {
            "startDate": f"{month_range_match.group(1)} {month_range_match.group(2)}",
            "endDate": month_range_match.group(3)
        }

    # Match single year
    single_year_match = re.search(r"\b(19\d\d|20\d\d)\b", text)
    if single_year_match:
        return {
            "startDate": single_year_match.group(1),
            "endDate": None
        }

    return {"startDate": None, "endDate": None}


def extract_projects_from_text(raw_text: str, extracted_skills: List[str]) -> List[Dict[str, Any]]:
    """Section-based project extraction identifying project name, description, tech stack, and URL."""
    projects = []
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]

    # Find project section start
    project_section_headers = [
        "projects", "academic projects", "personal projects",
        "major projects", "projects & work", "key projects"
    ]

    section_start = -1
    section_end = len(lines)

    for i, line in enumerate(lines):
        clean_line = line.lower().strip(":-#* ")
        if any(clean_line == header or clean_line.startswith(header) for header in project_section_headers):
            section_start = i + 1
            break

    if section_start != -1:
        # Find section end (next uppercase header)
        other_section_headers = [
            "education", "experience", "work experience", "skills",
            "certifications", "languages", "achievements", "interests"
        ]
        for j in range(section_start, len(lines)):
            clean_l = lines[j].lower().strip(":-#* ")
            if any(clean_l == h or clean_l.startswith(h) for h in other_section_headers):
                section_end = j
                break

        project_lines = lines[section_start:section_end]
        if project_lines:
            current_project: Optional[Dict[str, Any]] = None

            for line in project_lines:
                # Detect project URL if present
                url_match = re.search(r"https?://[^\s]+|github\.com/[^\s]+", line)
                line_url = url_match.group(0) if url_match else None

                # Check if this line looks like a project title (short, not starting with bullet or description words)
                is_bullet = line.startswith("-") or line.startswith("*") or line.startswith("•")
                if not is_bullet and len(line) < 60 and not line.lower().startswith("technologies") and not line.lower().startswith("tech stack"):
                    if current_project and current_project.get("name"):
                        projects.append(current_project)

                    current_project = {
                        "name": line.strip(":#-* "),
                        "description": "",
                        "technologies": [],
                        "url": line_url
                    }
                else:
                    if current_project is None:
                        current_project = {
                            "name": "Project",
                            "description": "",
                            "technologies": [],
                            "url": line_url
                        }

                    # Check for technologies line
                    tech_match = re.search(r"(?:tech(?:nologies|nology)?|stack|built with)\s*[:\-]\s*(.*)", line, re.IGNORECASE)
                    if tech_match:
                        tech_str = tech_match.group(1)
                        tech_list = [t.strip() for t in re.split(r"[,/|;]", tech_str) if t.strip()]
                        current_project["technologies"].extend(tech_list)
                    else:
                        # Append to description
                        cleaned_desc_line = line.strip(":-*• ")
                        if cleaned_desc_line:
                            if current_project["description"]:
                                current_project["description"] += " " + cleaned_desc_line
                            else:
                                current_project["description"] = cleaned_desc_line

                    if line_url and not current_project["url"]:
                        current_project["url"] = line_url

            if current_project and current_project.get("name"):
                projects.append(current_project)

    # Post-process projects to detect tech stack from extracted skills if missing
    for proj in projects:
        if not proj["technologies"] and proj["description"]:
            proj_techs = [
                skill for skill in extracted_skills
                if re.search(rf"\b{re.escape(skill)}\b", proj["description"], re.IGNORECASE)
            ]
            proj["technologies"] = proj_techs[:5]

        # Deduplicate tech list
        proj["technologies"] = list(dict.fromkeys(proj["technologies"]))

    return projects


def extract_skills_from_text(raw_text: str) -> List[str]:
    """Recover explicit skills and controlled technologies when NER is unavailable."""
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    candidates: List[str] = []
    for index, line in enumerate(lines):
        if re.match(r"(?i)^skills?\s*[:\-]", line):
            candidates.append(re.sub(r"(?i)^skills?\s*[:\-]\s*", "", line))
        elif re.match(r"(?i)^skills?$", line) and index + 1 < len(lines):
            candidates.append(lines[index + 1])
    values: List[str] = []
    for candidate in candidates:
        values.extend(value.strip() for value in re.split(r"[,|;/]", candidate) if value.strip())
    # Explicit skills retain backwards-compatible unknown entries; controlled
    # scanning additionally preserves technology evidence in projects/prose.
    return normalize_skills(values + extract_controlled_skills(raw_text))


def build_structured_resume(raw_text: str, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Combine NER entities and deterministic rules into normalized resume profile JSON."""
    
    # 1. Group NER entities by label
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for entity in entities:
        label = entity["label"]
        grouped.setdefault(label, []).append(entity)

    # 2. Extract Personal Information
    names = [e["text"] for e in grouped.get("NAME", [])]
    emails = [e["text"] for e in grouped.get("EMAIL", [])]
    phones = [e["text"] for e in grouped.get("PHONE", [])]
    locations = [e["text"] for e in grouped.get("LOCATION", [])]

    # Regex fallbacks for personal info if missing in NER
    if not emails:
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", raw_text)
        if email_match:
            emails.append(email_match.group(0))

    if not phones:
        phone_match = re.search(r"\(?\+?\d{1,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}", raw_text)
        if phone_match:
            phones.append(phone_match.group(0))

    name_str = names[0] if names else ""
    if not name_str:
        # Fallback to top non-contact lines
        lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
        for line in lines[:5]:
            if len(line) < 40 and not any(c.isdigit() for c in line) and "@" not in line and "http" not in line:
                name_str = line
                break

    personal = {
        "name": name_str or "Candidate Name",
        "email": emails[0] if emails else "",
        "phone": phones[0] if phones else "",
        "location": locations[0] if locations else ""
    }

    # 3. Academic Scores (SGPA / CGPA)
    academic_scores = extract_academic_scores(raw_text)

    # 4. Education Records
    degrees = [e["text"] for e in grouped.get("DEGREE", [])]
    fields = [e["text"] for e in grouped.get("FIELD", [])]
    institutions = [e["text"] for e in grouped.get("INSTITUTION", [])]
    dates = extract_dates_from_text(raw_text)

    education_records = []
    if degrees or institutions:
        degree_val = degrees[0] if degrees else "Degree / Qualification"
        field_val = fields[0] if fields else ""
        inst_val = institutions[0] if institutions else ""

        education_records.append({
            "degree": degree_val,
            "field": field_val,
            "institution": inst_val,
            "startDate": dates.get("startDate"),
            "endDate": dates.get("endDate"),
            "sgpa": academic_scores.get("sgpa"),
            "cgpa": academic_scores.get("cgpa")
        })
    else:
        # Check if education header exists in text
        if "education" in raw_text.lower():
            education_records.append({
                "degree": "Higher Education",
                "field": "General",
                "institution": "",
                "startDate": dates.get("startDate"),
                "endDate": dates.get("endDate"),
                "sgpa": academic_scores.get("sgpa"),
                "cgpa": academic_scores.get("cgpa")
            })

    # 5. Experience Records
    companies = [e["text"] for e in grouped.get("COMPANY", [])]
    titles = [e["text"] for e in grouped.get("TITLE", [])]

    experience_records = []
    if companies or titles:
        comp_val = companies[0] if companies else ""
        title_val = titles[0] if titles else ""
        exp_dates = extract_dates_from_text(raw_text)

        experience_records.append({
            "company": comp_val,
            "title": title_val,
            "startDate": exp_dates.get("startDate"),
            "endDate": exp_dates.get("endDate"),
            "duration": f"{exp_dates.get('startDate') or ''} - {exp_dates.get('endDate') or 'Present'}".strip(" -"),
            "description": ""
        })

    # 6. Skills (Normalized & Deduplicated)
    raw_skills = [e["text"] for e in grouped.get("SKILL", [])]
    normalized_skills = normalize_skills(raw_skills)
    # NER can be partial even when it succeeds, so merge the deterministic
    # evidence instead of using it only as an all-or-nothing fallback.
    normalized_skills = normalize_skills(normalized_skills + extract_skills_from_text(raw_text))

    # 7. Certifications
    certifications = list(dict.fromkeys([e["text"].strip() for e in grouped.get("CERT", []) if e["text"].strip()]))

    # 8. Languages
    languages = list(dict.fromkeys([e["text"].strip() for e in grouped.get("LANGUAGE", []) if e["text"].strip()]))

    # 9. Projects
    projects = extract_projects_from_text(raw_text, normalized_skills)

    # Final Normalized Profile Object
    return {
        "personal": personal,
        "education": education_records,
        "experience": experience_records,
        "skills": normalized_skills,
        "certifications": certifications,
        "languages": languages,
        "projects": projects,
        "rawEntities": entities
    }
