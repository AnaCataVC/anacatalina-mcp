"""
Pydantic data models for curriculum data validation and MCP tool outputs.
"""
from typing import List, Optional, Dict, Any
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
    name: str = Field(description="Display/CV name used professionally (Ana-Catalina Villalobos Contardo)")
    first_name: str = Field(default="Ana-Catalina", description="Nombre de pila / First name")
    middle_name: Optional[str] = Field(default="Alejandra", description="Segundo nombre / Middle name")
    last_name: str = Field(default="Villalobos Contardo", description="Apellidos / Last names")
    full_name: str = Field(
        default="Ana-Catalina Alejandra Villalobos Contardo",
        description="Nombre completo oficial / Full legal name"
    )
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


class PublicationItem(BaseModel):
    """Academic publication or research paper record."""
    id: str = Field(description="Unique identifier for the publication")
    title: str = Field(description="Publication title")
    journal: str = Field(description="Journal or publisher name")
    period: str = Field(description="Publication date or timeframe (e.g. Marzo 2021)")
    url: Optional[str] = Field(None, description="Public URL or DOI link")
    doi: Optional[str] = Field(None, description="Digital Object Identifier (DOI)")
    description: str = Field(description="Abstract or overview of research findings and methodology")


class FitEvaluationResult(BaseModel):
    """Automated job description fit analysis result."""
    target_role_detected: str = Field(description="Role detected or inferred from job description")
    estimated_fit_score: str = Field(description="Estimated match percentage or tier (e.g. 90% - Alto)")
    matching_strengths: List[str] = Field(description="Candidate strengths that match the job description")
    technologies_matched: List[str] = Field(description="Technologies mentioned in vacancy matching candidate's stack")
    added_value_summary: str = Field(description="Summary of high-impact contributions the candidate brings")


class SearchResult(BaseModel):
    """Structured output for cross-curriculum keyword search."""
    query: str = Field(description="Search term executed")
    matched_experiences_count: int = Field(description="Number of matching work experience entries")
    experiences: List[ExperienceItem] = Field(
        default_factory=list,
        description="Matching work experience items"
    )
    matched_skills: List[str] = Field(
        default_factory=list,
        description="Matching skill descriptions with level and category"
    )
    matched_projects_count: int = Field(description="Number of matching projects")
    projects: List[ProjectItem] = Field(
        default_factory=list,
        description="Matching project items"
    )
    matched_publications_count: int = Field(
        default=0,
        description="Number of matching publications"
    )
    publications: List[PublicationItem] = Field(
        default_factory=list,
        description="Matching publication items"
    )

    def __getitem__(self, item: str) -> Any:
        """Preserves dictionary-style indexing for backwards compatibility."""
        return getattr(self, item)


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
    publications: List[PublicationItem] = Field(default_factory=list)
