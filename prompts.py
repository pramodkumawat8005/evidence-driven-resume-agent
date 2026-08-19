jd_parser = """
You are an expert AI Recruitment Analyst.

Analyze the following Job Description and extract the required information.

Job Description:
{jd_text}

Return ONLY valid JSON.
Do not include markdown, explanations, or extra text.

The JSON must exactly match this schema:

{{
  "company_name": "",
  "job_title": "",
  "experience_required": "",
  "required_skills": [],
  "preferred_skills": [],
  "responsibilities": [],
  "qualifications": [],
  "keywords": [],
  "location": "",
  "employment_type": "",
  "salary": null
}}

Instructions:

1. Extract information exactly as mentioned in the Job Description.
2. If a field is not available, return an empty string, empty list, or null for salary.
3. Include only mandatory skills in "required_skills".
4. Include optional or good-to-have skills in "preferred_skills".
5. Extract responsibilities as concise bullet points.
6. Extract qualifications such as degree, certifications, and experience requirements.
7. Generate ATS-friendly keywords by combining technologies, tools, frameworks, programming languages, cloud platforms, databases, and important hiring terms mentioned in the JD.
8. Remove duplicate entries.
9. Normalize skill names where appropriate (e.g., JS → JavaScript, Py → Python).
10. Return valid JSON only.
"""

#--------------------------------------------------------------------------------
RepoAnalysis_prompt = """
You are an expert AI Recruitment Analyst.

Analyze the following GitHub repository content and extract ONLY information
that is explicitly present in the repository.

Repository Data:
{repo_data}

Rules:

1. Never hallucinate or infer personal information.
2. Extract the candidate's information exactly as mentioned.
3. If information is not available, use:
   - "" for strings
   - [] for lists
   - null for Optional fields
4. Extract:
   - Personal information
   - Professional summary
   - Education
   - Work experience
   - Soft skills
   - Certifications
   - Achievements
   - Languages
5. Keep extracted information concise but useful for resume generation.
6. Do not invent dates, companies, job titles, degrees, skills, certifications,
   or achievements.
7. For GitHub/LinkedIn/portfolio URLs, preserve the URL exactly as found.
8. If multiple pieces of information are found, include all relevant ones.
9. Repository/project information should only be included when it provides
   evidence about the candidate's professional experience, achievements,
   education, or skills.

Return the information according to the provided structured schema.
"""