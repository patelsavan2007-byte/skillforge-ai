export const TARGET_ROLES = [
  "AI/ML Engineer",
  "Data Scientist",
  "Data Analyst",
  "Data Engineer",
  "Software Engineer",
  "Frontend Developer",
  "Backend Developer",
  "Full Stack Developer",
  "Mobile App Developer",
  "DevOps Engineer",
  "Cloud Engineer",
  "Cybersecurity Engineer",
  "UI/UX Designer",
  "Product Manager",
  "QA Automation Engineer",
  "Blockchain Developer",
] as const;

export type TargetRole = (typeof TARGET_ROLES)[number];

export const ROLE_DESCRIPTIONS: Record<TargetRole, string> = {
  "AI/ML Engineer": "Build, deploy, and improve intelligent products using data and machine-learning models.",
  "Data Scientist": "Turn data into insights, experiments, and predictive business decisions.",
  "Data Analyst": "Explore data, build dashboards, and communicate clear business insights.",
  "Data Engineer": "Design dependable data pipelines, warehouses, and data platforms.",
  "Software Engineer": "Build reliable software systems with strong programming and problem-solving skills.",
  "Frontend Developer": "Create fast, accessible, polished web interfaces people enjoy using.",
  "Backend Developer": "Build APIs, databases, and secure services that power applications.",
  "Full Stack Developer": "Own complete web features from a refined interface to a robust backend.",
  "Mobile App Developer": "Create high-quality mobile experiences for Android and iOS.",
  "DevOps Engineer": "Automate delivery, infrastructure, observability, and reliable deployments.",
  "Cloud Engineer": "Build, migrate, and operate scalable cloud infrastructure.",
  "Cybersecurity Engineer": "Protect systems, applications, and data through secure engineering practices.",
  "UI/UX Designer": "Research user needs and design intuitive, attractive product experiences.",
  "Product Manager": "Shape product direction by connecting user needs, strategy, and delivery.",
  "QA Automation Engineer": "Create test systems that keep software releases dependable and fast.",
  "Blockchain Developer": "Build decentralized applications, smart contracts, and Web3 infrastructure.",
};

export const readiness = 68;

export const profileSummary =
  "You have a strong foundation in Python and Machine Learning with good project experience. Your biggest opportunities are Deep Learning, SQL and MLOps.";

export const extractedSkills = [
  { name: "Python", level: 90, required: 90 },
  { name: "Machine Learning", level: 75, required: 90 },
  { name: "Pandas", level: 85, required: 80 },
  { name: "NumPy", level: 85, required: 80 },
  { name: "C++", level: 70, required: 60 },
  { name: "SQL", level: 45, required: 80 },
  { name: "Deep Learning", level: 30, required: 90 },
  { name: "Docker", level: 20, required: 70 },
];

export const portfolioProjects = [
  {
    title: "Fashion Recommendation System",
    stack: "Python · Scikit-learn · Streamlit",
  },
  { title: "ML Dashboard", stack: "Pandas · Plotly · Flask" },
  { title: "Student Prediction System", stack: "Python · Regression · Pandas" },
];

export const portfolioFeedback =
  "Your projects demonstrate good ML fundamentals, but adding deployment and Deep Learning projects would strengthen your profile.";

export const skillGap = {
  strong: ["Python", "Pandas", "NumPy"],
  improve: ["Machine Learning", "SQL"],
  critical: ["Deep Learning", "MLOps", "Docker"],
};

export const roadmap = [
  {
    title: "Python",
    status: "done" as const,
    why: "Already demonstrated across your resume and three portfolio projects.",
    duration: "Completed",
    difficulty: "Beginner",
    skills: ["Syntax", "OOP", "Scripting"],
  },
  {
    title: "ML Fundamentals",
    status: "done" as const,
    why: "Your projects show solid classical machine learning understanding.",
    duration: "Completed",
    difficulty: "Intermediate",
    skills: ["Regression", "Classification", "Model Evaluation"],
  },
  {
    title: "Deep Learning",
    status: "current" as const,
    why: "Your resume shows ML experience but limited Deep Learning experience.",
    duration: "3 weeks",
    difficulty: "Advanced",
    skills: ["CNN", "Neural Networks", "Transfer Learning"],
  },
  {
    title: "SQL",
    status: "todo" as const,
    why: "Every AI/ML Engineer role you target lists SQL data access as a must-have.",
    duration: "2 weeks",
    difficulty: "Intermediate",
    skills: ["Joins", "Window Functions", "Query Optimization"],
  },
  {
    title: "MLOps & Docker",
    status: "todo" as const,
    why: "No deployment evidence found in your portfolio — this is a critical gap.",
    duration: "3 weeks",
    difficulty: "Advanced",
    skills: ["Docker", "CI/CD", "Model Serving", "Monitoring"],
  },
  {
    title: "Industry Capstone",
    status: "todo" as const,
    why: "A single end-to-end deployed project makes your resume interview-ready.",
    duration: "4 weeks",
    difficulty: "Advanced",
    skills: ["System Design", "Deployment", "Documentation"],
  },
];

export const courses = [
  {
    title: "Deep Learning Specialization",
    platform: "Coursera · DeepLearning.AI",
    skill: "Deep Learning",
    difficulty: "Advanced",
    duration: "3 months",
    why: "Large skill gap detected in your profile.",
  },
  {
    title: "SQL for Data Science",
    platform: "Coursera · UC Davis",
    skill: "SQL",
    difficulty: "Beginner",
    duration: "4 weeks",
    why: "Your SQL level (45%) is far below the 80% required for this role.",
  },
  {
    title: "Docker & Kubernetes: The Practical Guide",
    platform: "Udemy",
    skill: "Docker / MLOps",
    difficulty: "Intermediate",
    duration: "6 weeks",
    why: "No containerization signals found in your GitHub repositories.",
  },
  {
    title: "Machine Learning Engineering for Production",
    platform: "Coursera · DeepLearning.AI",
    skill: "MLOps",
    difficulty: "Advanced",
    duration: "2 months",
    why: "Bridges your ML knowledge into production-grade workflows.",
  },
  {
    title: "PyTorch for Deep Learning Bootcamp",
    platform: "Zero To Mastery",
    skill: "Neural Networks",
    difficulty: "Intermediate",
    duration: "5 weeks",
    why: "Hands-on practice to convert theory into portfolio projects.",
  },
];

export const projects = [
  {
    title: "Build an Image Classification System",
    difficulty: "Intermediate",
    time: "2 weeks",
    skills: ["CNN", "TensorFlow", "Computer Vision"],
    why: "This fills your Deep Learning gap and adds a strong AI project to your portfolio.",
    impact: "High resume impact",
  },
  {
    title: "Deploy an ML API with Docker + FastAPI",
    difficulty: "Intermediate",
    time: "10 days",
    skills: ["Docker", "FastAPI", "Model Serving"],
    why: "Proves you can ship models, the single biggest missing signal in your profile.",
    impact: "Very high resume impact",
  },
  {
    title: "Analytics Warehouse with SQL + dbt",
    difficulty: "Beginner",
    time: "1 week",
    skills: ["SQL", "Data Modeling", "Window Functions"],
    why: "Quickly lifts your weakest fundamental skill with a demonstrable artifact.",
    impact: "Medium resume impact",
  },
];

export const certifications = [
  {
    name: "TensorFlow Developer Certificate",
    provider: "Google",
    skill: "Deep Learning",
    difficulty: "Intermediate",
    why: "Validates the Deep Learning gap flagged in your analysis.",
  },
  {
    name: "AWS Certified Machine Learning – Specialty",
    provider: "Amazon Web Services",
    skill: "MLOps",
    difficulty: "Advanced",
    why: "Signals production ML capability that recruiters filter for.",
  },
  {
    name: "Docker Certified Associate",
    provider: "Docker",
    skill: "Containerization",
    difficulty: "Intermediate",
    why: "Directly addresses your 20% Docker score.",
  },
];

export const interviewTopics = {
  high: ["Deep Learning", "Machine Learning", "SQL", "Python"],
  medium: ["System Design", "Data Structures", "Statistics"],
  categories: [
    { name: "Technical", count: 14 },
    { name: "Coding", count: 12 },
    { name: "ML", count: 12 },
    { name: "SQL", count: 6 },
    { name: "Behavioral", count: 6 },
  ],
};

export const careerAdvice =
  "Focus on Deep Learning for the next 3 weeks, then strengthen SQL and MLOps. After completing these, build an image classification project and deploy it using Docker.";

export const progress = [
  { label: "Overall Career Readiness", value: 68, detail: "68%" },
  { label: "Roadmap", value: 33, detail: "2 / 6 completed" },
  { label: "Skills", value: 53, detail: "8 / 15 mastered" },
  { label: "Projects", value: 40, detail: "2 / 5 completed" },
];
