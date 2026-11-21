"""Health & Gold Analytics Dashboard DTOs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    postgres: Literal["up", "down"]
    duckdb: Literal["up", "down"]
    qdrant: Literal["up", "degraded", "down"]
    gold_competitions_count: int = 0


class KpiOverviewDTO(BaseModel):
    total_competitions: int
    open_competitions: int
    total_prize_pool_vnd: int
    free_participation_pct: float
    scholarship_competitions: int
    avg_team_size_max: float = 0.0
    unique_domains: int
    unique_organizers: int


class DomainMetricDTO(BaseModel):
    domain_slug: str
    domain_group: str
    competition_count: int
    allocated_prize_vnd: int
    free_count: int


class SeasonalityMetricDTO(BaseModel):
    year: int | None
    month: int | None
    academic_year: str
    academic_term: Literal["HK1", "HK2", "Hè", "Không xác định"]
    competition_count: int
    total_prize_vnd: int


class ModeTeamMetricDTO(BaseModel):
    mode_canonical: Literal["Online", "Offline", "Hybrid", "Unknown"]
    team_profile: str
    competition_count: int
    total_prize_vnd: int


class OrganizerMetricDTO(BaseModel):
    organizer_slug: str
    organizer_name: str
    organizer_tier: str
    role_type: Literal["organizer", "partner_sponsor"]
    competition_count: int
    allocated_prize_vnd: int


class AnalyticsDashboardDTO(BaseModel):
    kpi: KpiOverviewDTO
    domains: list[DomainMetricDTO]
    seasonality: list[SeasonalityMetricDTO]
    mode_team_matrix: list[ModeTeamMetricDTO]
    top_organizers: list[OrganizerMetricDTO]
