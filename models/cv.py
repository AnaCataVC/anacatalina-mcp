"""
Pydantic data models for curriculum data validation and MCP tool outputs.
"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class ContactDetails(BaseModel):
    """Direct contact channels."""
    email: str = Field(description="Direct email address")
    linkedin: str = Field(description="LinkedIn profile URL")


class PortfolioLinks(BaseModel):
    """Links to portfolio and repositories."""
    github: str = Field(description="GitHub profile URL")


class PersonalInfo(BaseModel):
    """General personal and headline information."""
    name: str = Field(description="Full name")
    title: str = Field(description="Professional headline / Current role")
    location: str = Field(description="Current location")
    contact: ContactDetails
    portfolio_links: PortfolioLinks


class ExperienceItem(BaseModel):
    """Work experience record."""
    company: str = Field(description="Company or organization name")
    role: str = Field(description="Job position or title")
    period: str = Field(description="Timeframe / Period of employment")
    location: str = Field(description="Workplace location / mode")
    type: str = Field(default="laboral", description="Experience type: laboral or personal")
    responsibilities: List[str] = Field(
        default_factory=list,
        description="Key responsibilities and functions performed"
    )
    technologies: List[str] = Field(
        default_factory=list,
        description="Technologies, libraries and tools used in this role"
    )


class SkillItem(BaseModel):
    """Specific skill with proficiency level."""
    name: str = Field(description="Skill or technology name")
    level: str = Field(description="Proficiency level (e.g., Avanzado, Intermedio)")


class SkillCategory(BaseModel):
    """Group of technical skills under a category."""
    category: str = Field(description="Category name")
    skills: List[SkillItem] = Field(default_factory=list, description="List of skills with levels")


class ProjectItem(BaseModel):
    """Featured project item."""
    name: str = Field(description="Project title")
    type: str = Field(description="Type of project: 'personal' or 'laboral'")
    description: str = Field(description="Project overview and purpose")
    technologies: List[str] = Field(
        default_factory=list,
        description="Technologies and frameworks used in the project"
    )
    repo_url: Optional[str] = Field(None, description="Public code repository URL if available")
    demo_url: Optional[str] = Field(None, description="Live demo or documentation URL if available")


class EducationItem(BaseModel):
    """Academic background record."""
    institution: str = Field(description="Academic institution name")
    degree: str = Field(description="Degree / Area of study")
    period: str = Field(description="Graduation year or study period")
    details: Optional[str] = Field(None, description="Relevant details or focus areas")


class FitEvaluationResult(BaseModel):
    """Automated job description fit analysis result."""
    target_role_detected: str = Field(description="Role detected or inferred from job description")
    estimated_fit_score: str = Field(description="Estimated match percentage or tier (e.g. 90% - Alto)")
    matching_strengths: List[str] = Field(description="Candidate strengths that match the job description")
    technologies_matched: List[str] = Field(description="Technologies mentioned in vacancy matching candidate's stack")
    added_value_summary: str = Field(description="Summary of high-impact contributions the candidate brings")


class CVData(BaseModel):
    """Complete root curriculum schema."""
    personal_info: PersonalInfo
    summary: Dict[str, str] = Field(
        default_factory=dict,
        description="Executive summaries keyed by language code ('es', 'en')"
    )
    experience: List[ExperienceItem] = Field(default_factory=list)
    skills: List[SkillCategory] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
