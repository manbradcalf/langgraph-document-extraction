"""Candidate screening interpretation for resumes.

Answers the screening questions used to evaluate applicants for roles
supporting women and families (admin, household management, childcare).
"""

from pydantic import Field

from docextract.schemas.base import DocumentSchema


class ExperienceArea(DocumentSchema):
    """A relevant experience area found on the resume."""

    area: str = Field(
        description=(
            "Category of relevant experience "
            "(e.g., 'admin', 'household management', 'childcare', 'eldercare')"
        )
    )
    evidence: str = Field(
        description="Short quote or summary from the resume supporting this area"
    )

    @classmethod
    def get_document_type(cls) -> str:
        return "experience_area"


class CandidateScreening(DocumentSchema):
    """Screening assessment of a candidate based on their resume."""

    market: str | None = Field(
        default=None,
        description="Metro area the candidate lives in, formatted 'City, State'",
    )

    is_parent: bool | None = Field(
        default=None,
        description=(
            "Whether the candidate is a parent, based on resume signals. "
            "Null if it cannot be inferred."
        ),
    )
    number_of_children: int | None = Field(
        default=None,
        description="Number of children mentioned, if stated. Null if unknown.",
    )

    years_of_experience: float | None = Field(
        default=None,
        description=(
            "Total years of relevant work experience across all roles. "
            "Null if work history is insufficient to estimate."
        ),
    )

    relevant_experience: list[ExperienceArea] = Field(
        default=[],
        description=(
            "Areas of relevant experience such as admin, household management, "
            "childcare, caregiving, personal assistance."
        ),
    )

    professional_tone: str = Field(
        description=(
            "Assessment of the candidate's written communication quality and "
            "professionalism based on the resume's language and structure."
        )
    )
    emotional_tone: str = Field(
        description=(
            "Assessment of empathy and warmth in the candidate's writing, "
            "particularly signals relevant to supporting women and families."
        )
    )

    red_flags: list[str] = Field(
        default=[],
        description=(
            "Potential concerns such as job hopping, unexplained gaps, "
            "or unclear work history. Empty if none identified."
        ),
    )

    summary: str = Field(
        description="Two-to-three sentence overall assessment of the candidate."
    )

    @classmethod
    def get_document_type(cls) -> str:
        return "candidate_screening"
