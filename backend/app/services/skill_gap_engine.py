"""
skill_gap_engine.py
===================
Deterministic Skill Gap Engine for SkillForge AI.

Core logic:
    user_strengths  = student_skills ∩ required_skills
    true_skill_gaps = required_skills − student_skills

All calculations are deterministic:
  - Case-insensitive normalization
  - Alias resolution for common spelling variants
  - Duplicate removal after normalization
  - Stable ordering (preserves required-skills order for gaps;
    preserves intersection order for strengths)

NO LLM is used at any stage of this module.
"""

import logging
from typing import List, Dict

logger = logging.getLogger("skillforge.skill_gap_engine")

# ---------------------------------------------------------------------------
# Deterministic alias map
# Maps lowercase variants -> canonical lowercase key used for matching.
# Canonical key matches the lowercased form of whatever appears in
# REQUIRED_SKILLS_BY_ROLE so that the display name is preserved from
# the required-skills list (not from the alias).
#
# Rules:
#   - Only include aliases that are unambiguously the same technology.
#   - "java" must NOT become "javascript".  They are separate languages.
#   - "react" must NOT become "react native".  They are separate frameworks.
#   - "aws" must NOT become "azure".  They are separate cloud providers.
#   - "sql" must NOT become "postgresql".  Generic vs specific DB.
#   - "ml" is NOT automatically "machine learning" — kept as-is.
# ---------------------------------------------------------------------------
SKILL_ALIASES: Dict[str, str] = {
    # ── Python ─────────────────────────────────────────────────────────────
    "python3": "python",
    "python 3": "python",

    # ── JavaScript / TypeScript ────────────────────────────────────────────
    "js": "javascript",
    "javascript (js)": "javascript",
    "ecmascript": "javascript",
    "ts": "typescript",
    "typescript (ts)": "typescript",

    # ── React (NOT React Native — kept separate) ───────────────────────────
    "reactjs": "react",
    "react.js": "react",
    "react js": "react",

    # ── Node.js ────────────────────────────────────────────────────────────
    "nodejs": "node.js",
    "node js": "node.js",
    "node": "node.js",

    # ── Express.js ─────────────────────────────────────────────────────────
    "express": "express.js",
    "expressjs": "express.js",
    "express js": "express.js",

    # ── Tailwind CSS ───────────────────────────────────────────────────────
    "tailwindcss": "tailwind css",
    "tailwind": "tailwind css",
    "tailwind-css": "tailwind css",

    # ── FastAPI ────────────────────────────────────────────────────────────
    "fast api": "fastapi",
    "fast-api": "fastapi",

    # ── MongoDB ────────────────────────────────────────────────────────────
    "mongo": "mongodb",
    "mongo db": "mongodb",

    # ── PostgreSQL ─────────────────────────────────────────────────────────
    "postgres": "postgresql",
    "postgre sql": "postgresql",

    # ── MySQL ──────────────────────────────────────────────────────────────
    "my sql": "mysql",

    # ── Git / Version Control ──────────────────────────────────────────────
    "github": "git",
    "gitlab": "git",
    "git/github": "git",

    # ── Kubernetes ─────────────────────────────────────────────────────────
    "k8s": "kubernetes",

    # ── Docker ─────────────────────────────────────────────────────────────
    "docker container": "docker",
    "containerization": "docker",

    # ── CI/CD ──────────────────────────────────────────────────────────────
    "ci cd": "ci/cd",
    "cicd": "ci/cd",
    "continuous integration": "ci/cd",
    "continuous delivery": "ci/cd",
    "continuous integration/continuous delivery": "ci/cd",

    # ── Machine Learning ───────────────────────────────────────────────────
    "machine-learning": "machine learning",

    # ── Deep Learning ──────────────────────────────────────────────────────
    "deep-learning": "deep learning",

    # ── Neural Networks ────────────────────────────────────────────────────
    "neural network": "neural networks",
    "neural net": "neural networks",

    # ── Natural Language Processing ────────────────────────────────────────
    "nlp": "natural language processing",
    "natural-language-processing": "natural language processing",

    # ── Computer Vision ────────────────────────────────────────────────────
    "computer-vision": "computer vision",

    # ── PyTorch ────────────────────────────────────────────────────────────
    "torch": "pytorch",
    "py torch": "pytorch",
    "py-torch": "pytorch",

    # ── TensorFlow ─────────────────────────────────────────────────────────
    "tf": "tensorflow",
    "tensor flow": "tensorflow",
    "tensor-flow": "tensorflow",

    # ── Scikit-learn ───────────────────────────────────────────────────────
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "scikit_learn": "scikit-learn",

    # ── NumPy ──────────────────────────────────────────────────────────────
    "np": "numpy",
    "num py": "numpy",

    # ── Pandas ─────────────────────────────────────────────────────────────
    "pd": "pandas",

    # ── Matplotlib ─────────────────────────────────────────────────────────
    "matplotlib pyplot": "matplotlib",

    # ── Power BI ───────────────────────────────────────────────────────────
    "powerbi": "power bi",
    "power-bi": "power bi",

    # ── Jupyter ────────────────────────────────────────────────────────────
    "jupyter notebook": "jupyter",
    "jupyter notebooks": "jupyter",
    "jupyter lab": "jupyter",
    "jupyterlab": "jupyter",

    # ── Excel ──────────────────────────────────────────────────────────────
    "microsoft excel": "excel",
    "ms excel": "excel",

    # ── Linux ──────────────────────────────────────────────────────────────
    "unix": "linux",
    "linux/unix": "linux",

    # ── Bash ───────────────────────────────────────────────────────────────
    "bash scripting": "bash",
    "shell scripting": "bash",
    "shell": "bash",

    # ── AWS ────────────────────────────────────────────────────────────────
    "amazon web services": "aws",
    "amazon aws": "aws",

    # ── Google Cloud ───────────────────────────────────────────────────────
    "gcp": "google cloud",
    "google cloud platform": "google cloud",

    # ── Infrastructure as Code ─────────────────────────────────────────────
    "iac": "infrastructure as code",

    # ── REST APIs ──────────────────────────────────────────────────────────
    "rest api": "rest apis",
    "restful apis": "rest apis",
    "restful api": "rest apis",
    "rest": "rest apis",

    # ── Data Structures ────────────────────────────────────────────────────
    "data structure": "data structures",
    "dsa": "data structures",

    # ── Object-Oriented Programming ────────────────────────────────────────
    "oop": "object-oriented programming",
    "object oriented programming": "object-oriented programming",
    "oops": "object-oriented programming",

    # ── Data Visualization ─────────────────────────────────────────────────
    "data-visualization": "data visualization",
    "data viz": "data visualization",
    "dataviz": "data visualization",

    # ── Data Analysis ──────────────────────────────────────────────────────
    "data-analysis": "data analysis",
    "data analytics": "data analysis",

    # ── Feature Engineering ────────────────────────────────────────────────
    "feature-engineering": "feature engineering",

    # ── Model Evaluation ───────────────────────────────────────────────────
    "model-evaluation": "model evaluation",
    "model assessment": "model evaluation",

    # ── Model Deployment ───────────────────────────────────────────────────
    "model-deployment": "model deployment",
    "model serving": "model deployment",

    # ── Data Preprocessing ─────────────────────────────────────────────────
    "data-preprocessing": "data preprocessing",
    "data pre-processing": "data preprocessing",

    # ── Data Cleaning ──────────────────────────────────────────────────────
    "data-cleaning": "data cleaning",
    "data cleansing": "data cleaning",

    # ── Statistics ─────────────────────────────────────────────────────────
    "stats": "statistics",
    "statistical analysis": "statistics",

    # ── Hypothesis Testing ─────────────────────────────────────────────────
    "hypothesis-testing": "hypothesis testing",
    "statistical testing": "hypothesis testing",

    # ── ETL ────────────────────────────────────────────────────────────────
    "extract transform load": "etl",

    # ── Data Pipelines ─────────────────────────────────────────────────────
    "data pipeline": "data pipelines",
    "data-pipelines": "data pipelines",

    # ── Data Warehousing ───────────────────────────────────────────────────
    "data warehouse": "data warehousing",
    "data-warehousing": "data warehousing",

    # ── Apache Spark ───────────────────────────────────────────────────────
    "apache spark": "apache spark",
    "spark": "apache spark",

    # ── Apache Airflow ─────────────────────────────────────────────────────
    "airflow": "apache airflow",

    # ── Kafka ──────────────────────────────────────────────────────────────
    "apache kafka": "kafka",

    # ── Hadoop ─────────────────────────────────────────────────────────────
    "apache hadoop": "hadoop",

    # ── Jenkins ────────────────────────────────────────────────────────────
    "jenkins ci": "jenkins",

    # ── GitHub Actions ─────────────────────────────────────────────────────
    "github-actions": "github actions",
    "gh actions": "github actions",

    # ── Terraform ──────────────────────────────────────────────────────────
    "terraform iac": "terraform",

    # ── Ansible ────────────────────────────────────────────────────────────
    "ansible automation": "ansible",

    # ── Monitoring ─────────────────────────────────────────────────────────
    "monitoring/observability": "monitoring",

    # ── IAM ────────────────────────────────────────────────────────────────
    "identity and access management": "iam",

    # ── Cybersecurity ──────────────────────────────────────────────────────
    "cyber security": "cybersecurity",
    "information security": "cybersecurity",
    "infosec": "cybersecurity",

    # ── Network Security ───────────────────────────────────────────────────
    "network-security": "network security",

    # ── Authentication ─────────────────────────────────────────────────────
    "auth": "authentication",

    # ── Authorization ──────────────────────────────────────────────────────
    "authz": "authorization",

    # ── JWT ────────────────────────────────────────────────────────────────
    "json web token": "jwt",
    "json web tokens": "jwt",

    # ── Cryptography ───────────────────────────────────────────────────────
    "crypto": "cryptography",

    # ── Penetration Testing ────────────────────────────────────────────────
    "pen testing": "penetration testing",
    "pentest": "penetration testing",
    "pen-test": "penetration testing",

    # ── OWASP ──────────────────────────────────────────────────────────────
    "owasp top 10": "owasp",

    # ── SIEM ───────────────────────────────────────────────────────────────
    "security information and event management": "siem",

    # ── Vulnerability Assessment ───────────────────────────────────────────
    "vulnerability-assessment": "vulnerability assessment",
    "vuln assessment": "vulnerability assessment",

    # ── Incident Response ──────────────────────────────────────────────────
    "incident-response": "incident response",

    # ── Risk Management ────────────────────────────────────────────────────
    "risk-management": "risk management",

    # ── Security Monitoring ────────────────────────────────────────────────
    "security-monitoring": "security monitoring",

    # ── API Security ───────────────────────────────────────────────────────
    "api-security": "api security",
    "api authentication": "api security",

    # ── HTML / CSS ─────────────────────────────────────────────────────────
    "html5": "html",
    "hypertext markup language": "html",
    "css3": "css",
    "cascading style sheets": "css",

    # ── Responsive Design ──────────────────────────────────────────────────
    "responsive web design": "responsive design",
    "responsive-design": "responsive design",

    # ── State Management ───────────────────────────────────────────────────
    "state-management": "state management",

    # ── Browser DevTools ───────────────────────────────────────────────────
    "browser developer tools": "browser devtools",
    "devtools": "browser devtools",
    "chrome devtools": "browser devtools",

    # ── Vite ───────────────────────────────────────────────────────────────
    "vitejs": "vite",
    "vite.js": "vite",

    # ── UI/UX Design ───────────────────────────────────────────────────────
    "user interface design": "ui design",
    "user experience design": "ux design",

    # ── Figma ──────────────────────────────────────────────────────────────
    "figma design": "figma",

    # ── Wireframing ────────────────────────────────────────────────────────
    "wireframe": "wireframing",
    "wireframes": "wireframing",

    # ── Prototyping ────────────────────────────────────────────────────────
    "prototype": "prototyping",

    # ── Usability Testing ──────────────────────────────────────────────────
    "usability-testing": "usability testing",
    "usability test": "usability testing",

    # ── Design Systems ─────────────────────────────────────────────────────
    "design system": "design systems",
    "design-systems": "design systems",

    # ── Interaction Design ─────────────────────────────────────────────────
    "ixd": "interaction design",
    "interaction-design": "interaction design",

    # ── Accessibility ──────────────────────────────────────────────────────
    "web accessibility": "accessibility",
    "a11y": "accessibility",

    # ── Information Architecture ───────────────────────────────────────────
    "information-architecture": "information architecture",

    # ── Product Management ─────────────────────────────────────────────────
    "product-management": "product management",

    # ── Agile ──────────────────────────────────────────────────────────────
    "agile methodology": "agile",
    "agile development": "agile",

    # ── Scrum ──────────────────────────────────────────────────────────────
    "scrum methodology": "scrum",

    # ── Product Roadmapping ────────────────────────────────────────────────
    "roadmapping": "product roadmapping",
    "product roadmap": "product roadmapping",

    # ── A/B Testing ────────────────────────────────────────────────────────
    "ab testing": "a/b testing",
    "a-b testing": "a/b testing",
    "split testing": "a/b testing",

    # ── Requirements Analysis ──────────────────────────────────────────────
    "requirements gathering": "requirements analysis",
    "requirements-analysis": "requirements analysis",

    # ── Stakeholder Management ─────────────────────────────────────────────
    "stakeholder-management": "stakeholder management",

    # ── Software Testing ───────────────────────────────────────────────────
    "software test": "software testing",
    "qa testing": "software testing",
    "quality assurance": "software testing",

    # ── Test Automation ────────────────────────────────────────────────────
    "automated testing": "test automation",
    "test-automation": "test automation",

    # ── Selenium ───────────────────────────────────────────────────────────
    "selenium webdriver": "selenium",

    # ── Cypress ────────────────────────────────────────────────────────────
    "cypress.io": "cypress",

    # ── Playwright ─────────────────────────────────────────────────────────
    "playwright test": "playwright",

    # ── API Testing ────────────────────────────────────────────────────────
    "api test": "api testing",
    "api tests": "api testing",

    # ── Postman ────────────────────────────────────────────────────────────
    "postman api": "postman",

    # ── Regression Testing ─────────────────────────────────────────────────
    "regression test": "regression testing",

    # ── Unit Testing ───────────────────────────────────────────────────────
    "unit test": "unit testing",
    "unit tests": "unit testing",

    # ── Integration Testing ────────────────────────────────────────────────
    "integration test": "integration testing",

    # ── Bug Tracking ───────────────────────────────────────────────────────
    "bug-tracking": "bug tracking",
    "issue tracking": "bug tracking",
    "defect tracking": "bug tracking",

    # ── Mobile ─────────────────────────────────────────────────────────────
    "android development": "android",
    "android sdk": "android",
    "ios development": "ios",
    "mobile-app-development": "mobile app development",
    "mobile development": "mobile app development",
    "mobile-ui": "mobile ui",
    "mobile user interface": "mobile ui",

    # ── React Native (distinct from React!) ────────────────────────────────
    "react-native": "react native",
    "reactnative": "react native",

    # ── Kotlin / Swift / Dart ─────────────────────────────────────────────
    "kotlin android": "kotlin",
    "swift ios": "swift",
    "dart flutter": "dart",

    # ── Firebase ───────────────────────────────────────────────────────────
    "google firebase": "firebase",

    # ── Blockchain ─────────────────────────────────────────────────────────
    "block chain": "blockchain",

    # ── Solidity ───────────────────────────────────────────────────────────
    "solidity smart contracts": "solidity",

    # ── Smart Contracts ────────────────────────────────────────────────────
    "smart contract": "smart contracts",

    # ── Web3 ───────────────────────────────────────────────────────────────
    "web 3": "web3",
    "web3.js": "web3",

    # ── Ethereum ───────────────────────────────────────────────────────────
    "eth": "ethereum",

    # ── Ethers.js ──────────────────────────────────────────────────────────
    "ethers": "ethers.js",
    "ether.js": "ethers.js",

    # ── Hardhat ────────────────────────────────────────────────────────────
    "hard hat": "hardhat",

    # ── Wallet Integration ─────────────────────────────────────────────────
    "crypto wallet": "wallet integration",

    # ── Distributed Systems ────────────────────────────────────────────────
    "distributed-systems": "distributed systems",
    "distributed computing": "distributed systems",

    # ── JSON ───────────────────────────────────────────────────────────────
    "json data": "json",

    # ── Database Fundamentals ──────────────────────────────────────────────
    "database": "database fundamentals",
    "databases": "database fundamentals",
    "db fundamentals": "database fundamentals",

    # ── Software Development ───────────────────────────────────────────────
    "software-development": "software development",

    # ── Debugging ──────────────────────────────────────────────────────────
    "debug": "debugging",

    # ── Testing (generic) ──────────────────────────────────────────────────
    "test": "testing",
    "tests": "testing",

    # ── Networking ─────────────────────────────────────────────────────────
    "computer networking": "networking",
    "network fundamentals": "networking",

    # ── Reporting ──────────────────────────────────────────────────────────
    "report writing": "reporting",

    # ── Dashboarding ───────────────────────────────────────────────────────
    "dashboard": "dashboarding",
    "dashboards": "dashboarding",

    # ── Documentation ──────────────────────────────────────────────────────
    "technical documentation": "documentation",
    "technical writing": "documentation",

    # ── Communication ──────────────────────────────────────────────────────
    "communication skills": "communication",

    # ── Next.js ────────────────────────────────────────────────────────────
    "next": "next.js",
    "nextjs": "next.js",
    "next js": "next.js",

    # ── Prisma ─────────────────────────────────────────────────────────────
    "prisma orm": "prisma",
    "prisma client": "prisma",

    # ── Mongoose ───────────────────────────────────────────────────────────
    "mongoose odm": "mongoose",
    "mongoose orm": "mongoose",

    # ── Flask ──────────────────────────────────────────────────────────────
    "flask api": "flask",
    "python flask": "flask",

    # ── Django ─────────────────────────────────────────────────────────────
    "django rest framework": "django",
    "django drf": "django",

    # ── GraphQL ────────────────────────────────────────────────────────────
    "graphql api": "graphql",
    "graph ql": "graphql",

    # ── Redis ──────────────────────────────────────────────────────────────
    "redis cache": "redis",

    # ── System Design ──────────────────────────────────────────────────────
    "system-design": "system design",
    "systems design": "system design",
    "software architecture": "system design",

    # ── Microservices ──────────────────────────────────────────────────────
    "microservice": "microservices",
    "micro services": "microservices",
    "micro-services": "microservices",

    # ── Full Stack ─────────────────────────────────────────────────────────
    "full-stack": "full stack",
    "fullstack": "full stack",
    "full stack development": "full stack",

    # ── Frontend/Backend Development ───────────────────────────────────────
    "front-end": "frontend development",
    "front end": "frontend development",
    "front-end development": "frontend development",
    "back-end": "backend development",
    "back end": "backend development",
    "back-end development": "backend development",

    # ── AWS services ───────────────────────────────────────────────────────
    "aws s3": "aws",
    "aws ec2": "aws",
    "aws lambda": "aws",

    # ── Vercel / Netlify ───────────────────────────────────────────────────
    "vercel deployment": "vercel",
    "netlify deployment": "netlify",
}


def normalize_skill(skill: str) -> str:
    """
    Normalize a single skill string deterministically.

    Steps:
    1. Strip surrounding whitespace.
    2. Lowercase.
    3. Apply alias resolution if an alias entry matches.

    Returns the canonical lowercase form used for matching.
    The display name is always taken from the *required* skills list, not here.
    """
    if not isinstance(skill, str):
        return ""
    cleaned = skill.strip().lower()
    return SKILL_ALIASES.get(cleaned, cleaned)


def normalize_skill_list(skills: List[str]) -> List[str]:
    """
    Normalize a list of skills:
    - Apply normalize_skill to each entry.
    - Remove empty strings.
    - Deduplicate (first occurrence wins, preserving order).

    Returns a list of canonical lowercase skill strings.
    """
    seen: set = set()
    result: List[str] = []
    for s in skills:
        norm = normalize_skill(s)
        if norm and norm not in seen:
            seen.add(norm)
            result.append(norm)
    return result


def compute_skill_gap(
    student_skills: List[str],
    required_skills: List[str],
) -> Dict[str, List[str]]:
    """
    Deterministic skill gap calculation.

    Parameters
    ----------
    student_skills  : Raw list of skills extracted from student profile.
    required_skills : Raw list of skills required for the target role.

    Returns
    -------
    {
        "user_strengths":  [...],   # student_skills intersection required_skills
        "true_skill_gaps": [...],   # required_skills minus student_skills
        "matched_skills":  [...],   # alias for user_strengths (compat)
        "missing_skills":  [...],   # alias for true_skill_gaps (compat)
        "student_skills_normalized":  [...],
        "required_skills_normalized": [...],
    }

    Display names in user_strengths and true_skill_gaps are taken from
    the *required_skills* list (preserving the project's canonical casing),
    not from the student's raw input.

    Ordering
    --------
    - user_strengths  : order of appearance in required_skills
    - true_skill_gaps : order of appearance in required_skills

    Edge cases
    ----------
    - Empty student_skills  -> user_strengths = [], true_skill_gaps = all required
    - Empty required_skills -> user_strengths = [], true_skill_gaps = []
    - All match             -> user_strengths = all required, true_skill_gaps = []

    Consistency guarantee
    ---------------------
    A skill NEVER appears in both user_strengths AND true_skill_gaps.
    The result is a strict partition of required_skills.
    """
    # Normalize student skill set (for O(1) lookup)
    student_norm_set = set(normalize_skill_list(student_skills))

    # Build (display_name -> norm_key) for required skills in order
    required_norm_ordered: List[str] = []   # normalized keys in required order
    required_display: Dict[str, str] = {}   # norm_key -> display name (first seen)

    for req in required_skills:
        norm_key = normalize_skill(req)
        if norm_key and norm_key not in required_display:
            required_norm_ordered.append(norm_key)
            required_display[norm_key] = req.strip()   # preserve original casing

    # Deterministic set operations — pure partition, zero overlap by construction
    user_strengths: List[str] = []
    true_skill_gaps: List[str] = []

    for norm_key in required_norm_ordered:
        display = required_display[norm_key]
        if norm_key in student_norm_set:
            user_strengths.append(display)
        else:
            true_skill_gaps.append(display)

    # ── Safety assertion ──────────────────────────────────────────────────
    # By construction these sets are always disjoint.  Log an error if not.
    strengths_lower = set(s.lower() for s in user_strengths)
    gaps_lower = set(s.lower() for s in true_skill_gaps)
    overlap = strengths_lower & gaps_lower
    if overlap:
        logger.error(
            "INVARIANT VIOLATION: skill(s) appear in both strengths and gaps: %s",
            overlap,
        )

    logger.info(
        "Skill gap computed — strengths: %d, gaps: %d "
        "(student had %d normalized skills, role requires %d)",
        len(user_strengths),
        len(true_skill_gaps),
        len(student_norm_set),
        len(required_norm_ordered),
    )

    return {
        "user_strengths": user_strengths,
        "true_skill_gaps": true_skill_gaps,
        # Backward-compatible aliases so downstream code keeps working
        "matched_skills": user_strengths,
        "missing_skills": true_skill_gaps,
        # Diagnostic fields for debugging / downstream use
        "student_skills_normalized": sorted(student_norm_set),
        "required_skills_normalized": [required_display[k] for k in required_norm_ordered],
    }
