from typing import List, Optional, Literal, Dict, TypedDict
from pydantic import BaseModel, Field

class ExperienceRequirement(BaseModel):
    minimum_years: Optional[int] = None
    maximum_years: Optional[int] = None

class JDData(BaseModel):
    company_name: str = ""
    job_title: str = ""

    experience_required: ExperienceRequirement = Field(
        default_factory=ExperienceRequirement
    )

    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)

    responsibilities: List[str] = Field(default_factory=list)
    qualifications: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)

    location: str = ""
    employment_type: str = ""

    salary: Optional[str] = None


# git personal info repo get information


class PersonalInformation(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""

    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    website: Optional[str] = None


# =========================
# Education
# =========================
class Education(BaseModel):
    degree: str = ""
    specialization: Optional[str] = None

    institution: str = ""
    university: str = ""
    location: Optional[str] = None

    start_date: str = ""
    end_date: Optional[str] = None

    is_current: bool = False

    cgpa: Optional[str] = None
    percentage: Optional[str] = None


# =========================
# Experience
# =========================
class Experience(BaseModel):
    job_title: str = ""
    company: str = ""

    start_date: str = ""
    end_date: Optional[str] = None

    currently_working: bool = False

    responsibilities: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)

# =========================
# Certifications
# =========================

class Certification(BaseModel):
    name: str = ""
    issuer: str = ""
    date: Optional[str] = None


# =========================
# Resume Data
# =========================

class PersonalRepoData(BaseModel):
    personal_information: PersonalInformation

    professional_summary: str = ""

    education: List[Education] = Field(default_factory=list)
    experience: List[Experience] = Field(default_factory=list)
    
    soft_skills: List[str] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)



class TechnicalSkills(BaseModel):
    programming_languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    libraries: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    cloud: List[str] = Field(default_factory=list)
    devops: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    ml: List[str] = Field(default_factory=list)
    deep_learning:List[str] = Field(default_factory=list)
    gen_ai: List[str] = Field(default_factory=list)
    agentic_ai: List[str] = Field(default_factory=list)
    other: List[str] = Field(default_factory=list)
# =========================
# Projects
# =========================

class Project(BaseModel):
    project_name: str = ""
    description: str = ""

    features: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)

    github: Optional[str] = None
    live_demo: Optional[str] = None

    evidence: List[str] = Field(default_factory=list)

class RepoAnalysis(BaseModel):
    technical_skills: TechnicalSkills   
    projects: List[Project] = Field(default_factory=list)


class mainstate(TypedDict):
    RepoAnalysis=RepoAnalysis
    PersonalRepoData=PersonalRepoData
    JDData=JDData
    profile_reponame: str = ""
    relevant_repo_urls: List[str] = Field(default_factory=list)


