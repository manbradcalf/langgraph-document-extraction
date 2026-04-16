"""Resume schema for job-application screening."""

from datetime import date

from pydantic import Field

from docextract.schemas.base import DocumentSchema


class WorkExperience(DocumentSchema):
    """A single role on a resume."""

    employer: str = Field(description="Company or family name")
    role: str = Field(description="Job title / position")
    start_date: date | None = None
    end_date: date | None = Field(
        default=None, description="End date; null if current role"
    )
    is_current: bool = Field(
        default=False, description="True if this is the candidate's current role"
    )
    description: str | None = Field(
        default=None,
        description="Responsibilities, accomplishments, and any relevant detail",
    )

    @classmethod
    def get_document_type(cls) -> str:
        return "work_experience"


class Education(DocumentSchema):
    """A single education entry."""

    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    graduation_date: date | None = None

    @classmethod
    def get_document_type(cls) -> str:
        return "education"


class Resume(DocumentSchema):
    """Resume data extracted from a candidate's document."""

    # Contact information
    first_name: str = Field(description="Candidate's first/given name")
    last_name: str = Field(description="Candidate's last/family name")
    email: str | None = Field(default=None, description="Primary email address")
    phone: str | None = Field(default=None, description="Primary phone number")

    # Location
    street_address: str | None = None
    city: str | None = None
    state: str | None = Field(
        default=None, description="State or region (e.g., 'NY', 'California')"
    )
    market: str | None = Field(
        default=None,
        description="Metro area or market, typically 'City, State' (e.g., 'Austin, TX')",
    )

    # Narrative
    summary: str | None = Field(
        default=None, description="Professional summary or objective, if present"
    )

    # History
    work_experience: list[WorkExperience] = Field(
        default=[], description="All work history listed on the resume"
    )
    education: list[Education] = Field(
        default=[], description="All education listed on the resume"
    )

    skills: list[str] = Field(
        default=[], description="Skills, tools, or areas of expertise"
    )
    certifications: list[str] = Field(
        default=[], description="Certifications and licenses"
    )
    languages: list[str] = Field(
        default=[], description="Spoken or written languages"
    )

    @classmethod
    def get_document_type(cls) -> str:
        return "resume"
