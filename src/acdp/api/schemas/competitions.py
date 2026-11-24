"""Competition Explorer & Detail DTOs."""

from __future__ import annotations

from pydantic import BaseModel


class CompetitionSummaryDTO(BaseModel):
    competition_key: str
    name: str
    tagline: str | None = None
    canonical_url: str
    mode_canonical: str
    is_free: bool
    total_prize_vnd: int
    has_scholarship: bool = False
    registration_status: str | None = None
    registration_deadline_raw: str | None = None
    domain_groups: list[str]
    domain_slugs: list[str] = []
    team_size_min: int | None = None
    team_size_max: int | None = None
    team_profile: str | None = None


class PrizeTierDTO(BaseModel):
    tier_rank: int
    tier_name: str
    reward_description: str
    estimated_value_vnd: int
    is_scholarship: bool


class TimelineStageDTO(BaseModel):
    stage_order: int
    stage_name: str
    start_date_raw: str | None = None
    end_date_raw: str | None = None
    description: str | None = None


class CompetitionDetailDTO(CompetitionSummaryDTO):
    summary: str | None = None
    target_audience: str | None = None
    location: str | None = None
    submission_platform: str | None = None
    challenge_overview: str | None = None
    organizers: list[str]
    partners_and_sponsors: list[str]
    prizes: list[PrizeTierDTO]
    timeline_stages: list[TimelineStageDTO]


class PaginatedCompetitionsDTO(BaseModel):
    items: list[CompetitionSummaryDTO]
    total: int
    page: int
    page_size: int
