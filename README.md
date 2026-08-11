# SkillForge-Ai

Build a frontend-only hackathon project called "SkillForge AI".

PROBLEM:

AI-powered personalized learning and career mentor for students.

IMPORTANT:

I want a SIMPLE, polished MVP.

Do NOT create many pages.

Use only 3 main pages/screens.

Do NOT build backend, database, Gemini API, authentication, or real AI yet.

Use realistic mock data.

I will connect my own FastAPI + Gemini backend later.

==================================================

CORE USER FLOW

==================================================

Student provides:

1. Resume PDF

2. Portfolio/GitHub URL

3. Target Career/Job Role

Example:

Resume:

[ Upload Resume.pdf ]

Portfolio:

[ https://github.com/student ]

Target Role:

[ AI/ML Engineer ▼ ]

[ Analyze My Profile ]

Then show AI-generated results.

==================================================

PAGE 1 — HOME / PROFILE INPUT

==================================================

Create a beautiful landing + input page in one screen.

Hero:

"SkillForge AI"

"Your AI-powered career mentor"

Subtitle:

"Upload your resume, share your portfolio, and discover exactly what you should learn next to become job-ready."

Input section:

--------------------------------

RESUME

--------------------------------

Drag & drop PDF

[ Upload Resume ]

Show:

✓ filename

✓ file size

✓ remove button

--------------------------------

PORTFOLIO

--------------------------------

Input field:

GitHub / Portfolio URL

Example:

https://github.com/username

Also allow:

LinkedIn URL (optional)

--------------------------------

TARGET CAREER

--------------------------------

Dropdown:

AI/ML Engineer

Data Scientist

Software Engineer

Full Stack Developer

Data Analyst

Cybersecurity Engineer

Button:

"Analyze My Career"

Use mock loading animation after clicking.

Then navigate to Page 2.

==================================================

PAGE 2 — AI PROFILE ANALYSIS

==================================================

This page should contain ALL important analysis in ONE dashboard.

Header:

"Your Career Analysis"

Show:

Career Readiness

68%

Target:

AI/ML Engineer

--------------------------------

PROFILE SUMMARY

--------------------------------

AI-generated summary:

"You have a strong foundation in Python and Machine Learning with good project experience. Your biggest opportunities are Deep Learning, SQL and MLOps."

--------------------------------

EXTRACTED SKILLS

--------------------------------

Display skill cards/bars:

Python          90%

Machine Learning 75%

Pandas           85%

NumPy            85%

C++              70%

SQL              45%

Deep Learning    30%

Docker           20%

--------------------------------

PORTFOLIO ANALYSIS

--------------------------------

Show projects detected from portfolio:

✓ Fashion Recommendation System

✓ ML Dashboard

✓ Student Prediction System

Show AI feedback:

"Your projects demonstrate good ML fundamentals, but adding deployment and Deep Learning projects would strengthen your profile."

--------------------------------

SKILL GAP

--------------------------------

Show:

Strong Skills:

✓ Python

✓ Pandas

✓ NumPy

Needs Improvement:

⚠ Machine Learning

⚠ SQL

Critical Gaps:

🔴 Deep Learning

🔴 MLOps

🔴 Docker

Show a simple comparison:

YOUR LEVEL vs REQUIRED LEVEL

Use progress bars.

--------------------------------

Button:

"Generate My Personalized Plan"

==================================================

PAGE 3 — PERSONALIZED CAREER PLAN

==================================================

This is the MAIN WOW page.

Title:

"Your Personalized Career Plan"

Target:

AI/ML Engineer

Show everything in ONE page using sections/tabs/cards.

--------------------------------

1. LEARNING ROADMAP

--------------------------------

Create a visual timeline:

✓ Python

✓ ML Fundamentals

↓

🔥 Deep Learning

↓

SQL

↓

MLOps & Docker

↓

Industry Capstone

Each item should show:

Why you need it

Estimated duration

Difficulty

Skills covered

Example:

🔥 Deep Learning

Why:

"Your resume shows ML experience but limited Deep Learning experience."

Duration:

3 weeks

Skills:

CNN

Neural Networks

Transfer Learning

--------------------------------

2. COURSE RECOMMENDATIONS

--------------------------------

Show 3-5 personalized course cards.

Each card:

Course title

Platform/source

Skill

Difficulty

Duration

Why recommended

[View Course]

Example:

Deep Learning Specialization

Skill:

Deep Learning

Why recommended:

"Large skill gap detected in your profile."

--------------------------------

3. PROJECT RECOMMENDATIONS

--------------------------------

Show 3 personalized projects.

Each:

Project title

Difficulty

Estimated time

Skills gained

Why recommended

Resume impact

Example:

"Build an Image Classification System"

Skills:

CNN

TensorFlow

Computer Vision

Why:

"This fills your Deep Learning gap and adds a strong AI project to your portfolio."

--------------------------------

4. CERTIFICATION RECOMMENDATIONS

--------------------------------

Show 2-3 certifications.

Include:

Name

Provider

Skill

Difficulty

Why recommended

[View]

--------------------------------

5. INTERVIEW PREPARATION

--------------------------------

Show recommended interview topics based on skill gaps.

Example:

High Priority:

- Deep Learning

- Machine Learning

- SQL

- Python

Show:

"50 personalized interview questions"

Categories:

Technical

Coding

ML

SQL

Behavioral

Button:

"Start Interview Prep"

--------------------------------

6. AI CAREER ADVICE

--------------------------------

At bottom show an AI-generated summary:

"Your next best step"

Example:

"Focus on Deep Learning for the next 3 weeks, then strengthen SQL and MLOps. After completing these, build an image classification project and deploy it using Docker."

--------------------------------

PROGRESS

--------------------------------

Show a simple progress section:

Overall Career Readiness:

68%

Roadmap:

2 / 6 completed

Skills:

8 / 15 mastered

Projects:

2 / 5 completed

==================================================

IMPORTANT AI/RECOMMENDATION CONCEPT

==================================================

The frontend should visually represent this logic:

RESUME + PORTFOLIO + TARGET ROLE

                ↓

        AI PROFILE ANALYSIS

                ↓

          CURRENT SKILLS

                ↓

      COMPARE WITH ROLE SKILLS

                ↓

           SKILL GAPS

                ↓

       PERSONALIZED ROADMAP

                ↓

 ┌──────────────┼──────────────┐

 ↓              ↓              ↓

Courses       Projects      Certifications

                ↓

         Interview Questions

                ↓

         Career Improvement

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/969e3d26-8ed9-4fe9-97bb-b681bb6ac483).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
