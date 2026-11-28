# Graph Report - acdp-platform  (2026-11-28)

## Corpus Check
- 283 files · ~332,192 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: (none) 6, .example 1, .api 1)

## Summary
- 2347 nodes · 4494 edges · 161 communities (121 shown, 40 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 290 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- V2 URL Discovery
- Analytics API Router
- V2 Silver Transform
- Ollama Validation Bridge
- JWT Auth & Seeding
- Auth & Bookmarks Tests
- Gold Star Schema
- Admin & DuckDB Refresh
- Cloud Environment Config
- V2 Pydantic Schemas
- Next.js Web Dependencies
- Student Profile Router
- V1 Pydantic Schemas
- FastAPI CORS & Seeding
- Crawl4AI Web Crawler
- RAG Chat Router
- Bronze Storage Evaluation
- Dual-Layer RAG Retrieval
- PostgreSQL OLTP Models
- Web App Layout & Fonts
- RFC-0001 & BI Boundary
- Admin UI & API Client
- Web Portal Pages
- V1 Gold Analytics
- AppSettings & R2 Config
- RAG Service & Fallback
- Cloud Ops & R2 Client
- AI Slop Linter
- Doc Drift Auditor
- Two-Tier Gold & RAG
- V2 Silver Transform Tests
- Gold Star Schema Tests
- Competition Cards & Detail
- Analytics Dashboard Page
- Security Middleware Exports
- R2 CV PDF Storage
- Qdrant Vector Store
- OWASP Security Tests
- Gold Dimension Builders
- SWOT & Slide Validators
- V1 LLM Extraction
- Gold Metadata Pre-Filtering
- TypeScript Compiler Config
- TLCN Thesis Report
- Academic Term & Date Keys
- Gold DDL & R2 Sync
- Asyncpg & Supabase Engine
- Silver Progress Presentation
- Hybrid Sandwich & Ragas
- Prefect Medallion Flow
- Cloudflare BGE-M3 Embedder
- In-Repo Task Sync
- R2 & Backup Env Vars
- RAG & OpenAPI Tests
- QA Tech Decision Tests
- V2 RAG Ingestion
- Academic Research Skill
- Delivery Gate Validator
- DuckDB R2 Client
- Multi-Tier Rate Limiter
- FastAPI Auth Dependencies
- OpenAPI Schema Exporter
- Silver R2 Payload Loader
- Docker Compose Services
- Cloudflare Workers Embeddings
- Doc Drift Audit Tests
- Competitions Explorer Page
- Copilot Workspace Page
- Web & Gold Stack R&D
- Profile Request Validation
- LLM & Qdrant Settings
- Docker & Infra Tests
- Workers AI Embeddings Dup
- Silver Schema Unit Tests
- Anti-Slop Scientific Skill
- Docker Build & Profiles
- Web Container Env Config
- V2 Discovery Unit Tests
- Postgres Container Env
- Visual Dossier & Delivery
- Thesis Formatting Validator
- Prefect Container Config
- Architecture Diagram Core
- GitHub Actions Steps
- Ollama Chatbot Integration
- Weekly pg_dump Workflow
- Adaptive Crawler Patches
- BM25 Hybrid Retriever
- Container Resource Limits
- Metabase Container Env
- Qdrant Container Config
- Medallion Layer Deliverables
- Keep-Alive & DQ Workflow
- RAG Response TTL Cache
- Bronze Purity & R2 Audit
- Full Cloud Stack Summary
- ADR-0002 Free-Tier Cloud
- Security Gates & HF-01
- Literature & SOTA Matrix
- Frontend Design Validator
- Container Healthchecks
- TLCN Proposal & Scope
- VectorRAG & GraphRAG
- Silver Schema v2 Gaps
- Ragas 3-System Ablation
- Feasibility & T01 Review
- Competition Landscape Survey
- Query Space Mapping
- Percentile Semantic Chunker
- Agent Operating Contracts
- Web Sprint 02 Deliverables
- API Test Fixtures
- R2 Gold Pipeline Verify
- Deliverable Template & Runbook
- Local Dev & Admin Docs
- Specs & Sprint Planning
- Cloud & Infra Deliverables
- Workflow Input Parameters
- Weekly Backup Job Config
- Rate Limit Telemetry
- Vercel Proxy & TTL Cache
- Gemini Workspace Directives
- V2 Medallion Topology
- Skill & Prompt Frameworks
- DIR-018 Task Registry
- Academic & Ops Layer
- Qdrant Collection Setup
- Qdrant Failover & RAM
- Competitor Benchmark Skill
- Defense Pitch Skill
- Student Mini-CV Profile
- Claude Code Guardrails
- PostCSS Configuration
- Web Favicon SVG
- Team Role Matching
- ACDP Architecture Diagram
- R2 & DuckDB Core
- Deliverables Ledger Sync
- Market Research Index
- RFC Change Process
- ADR-0001 Inception Stack
- ADR-0002 Cloud Defense
- TLCN vs KLTN Phases
- 3-Tier Discovery Layer
- DIR-011 Tabula Rasa
- DIR-012 Temporal Anchor
- DIR-015 Lean TLCN Scope
- DIR-017 Zero Doc Drift
- DIR-023 TLCN-KLTN Tiering
- ACDP Package Stub

## God Nodes (most connected - your core abstractions)
1. `User` - 49 edges
2. `environment` - 48 edges
3. `AppConfig` - 46 edges
4. `Competition` - 28 edges
5. `build_gold_star_schema()` - 23 edges
6. `build_gold_star_schema()` - 22 edges
7. `next` - 20 edges
8. `react` - 20 edges
9. `Competition` - 20 edges
10. `lucide-react` - 18 edges

## Surprising Connections (you probably didn't know these)
- `test_g4_ai_rate_limiting_per_user_day_and_global_rpm()` --uses--> `MultiTierRateLimiter`  [INFERRED]
  tests/api/test_security_owasp.py → src/acdp/api/middleware/security.py
- `test_g7_security_headers_and_global_exception_masking()` --uses--> `SecurityHardeningMiddleware`  [INFERRED]
  tests/api/test_security_owasp.py → src/acdp/api/middleware/security.py
- `test_rag_chat_persistence_ungrounded_and_outage()` --uses--> `RagCitationDTO`  [INFERRED]
  tests/api/test_rag_and_openapi.py → src/acdp/api/schemas/rag.py
- `test_g4_ai_rate_limiting_per_user_day_and_global_rpm()` --uses--> `RagCitationDTO`  [INFERRED]
  tests/api/test_security_owasp.py → src/acdp/api/schemas/rag.py
- `test_profile_pdf_upload_download_delete_and_privacy()` --indirect_call--> `get_cv_storage_service()`  [INFERRED]
  tests/api/test_profile.py → src/acdp/api/services/cv_storage.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **AI Agent Governance & Workspace Contracts** — agents_operating_contract, claude_standing_brief, gemini_workspace_rules, agents_skills_readme_registry [EXTRACTED 1.00]
- **ACDP v2 Medallion Lakehouse & Serving Flow** — readme_three_tier_discovery, readme_bronze_layer, readme_silver_layer, readme_gold_layer, readme_dual_layer_rag, readme_serving_web_oltp, readme_cloud_ops [EXTRACTED 1.00]
- **Core Team Standing Directives** — agents_dir_011_tabula_rasa, agents_dir_012_temporal_grounding, agents_dir_015_lean_tlcn_stack, agents_dir_016_oltp_olap_split, agents_dir_017_atomic_decision_sync, agents_dir_018_in_repo_tasks, agents_dir_022_v2_pipeline_scope, agents_dir_023_tlcn_kltn_tiering, agents_dir_024_delivery_gate [EXTRACTED 1.00]
- **Medallion Data Pipeline Flow** — docs_assets_arch_competition_sources, docs_assets_arch_bronze_layer, docs_assets_arch_silver_layer, docs_assets_arch_gold_layer, docs_assets_arch_serving_layer [EXTRACTED 1.00]
- **Traditional VectorRAG Pipeline** — docs_assets_arch_chunking, docs_assets_arch_embedding, docs_assets_arch_vectordb, docs_assets_arch_llm [EXTRACTED 1.00]
- **GraphRAG Extraction Pipeline** — docs_assets_arch_chunking, docs_assets_arch_llm_gliner, docs_assets_arch_ontology_triples, docs_assets_arch_knowledge_graph [EXTRACTED 1.00]
- **Bronze Object Storage Candidates Evaluated** — docs_deliverables_nt_018_bronze_storage_and_table_format_evaluation_local_posix, docs_deliverables_nt_018_bronze_storage_and_table_format_evaluation_seaweedfs, docs_deliverables_nt_018_bronze_storage_and_table_format_evaluation_minio, docs_deliverables_nt_018_bronze_storage_and_table_format_evaluation_cloudflare_r2 [EXTRACTED 1.00]
- **Open Table Format Candidates Evaluated** — docs_deliverables_nt_018_bronze_storage_and_table_format_evaluation_delta_lake, docs_deliverables_nt_018_bronze_storage_and_table_format_evaluation_apache_iceberg, docs_deliverables_nt_018_bronze_storage_and_table_format_evaluation_lance_format, docs_deliverables_nt_018_bronze_storage_and_table_format_evaluation_apache_hudi [EXTRACTED 1.00]
- **Cycle 06 Medallion v2 Pipeline (Discovery -> Silver -> Two-Tier Gold -> Dual-Layer RAG)** — docs_deliverables_task_ing_03_three_tier_discovery_implementation_discovery_v2_module, docs_deliverables_task_slv_01_hybrid_de_vs_llm_extraction_study_deterministic_sandwich, docs_deliverables_task_slv_02_silver_schema_and_parquet_validation_visual_dossier_dossier, docs_deliverables_task_gld_02_two_tier_gold_and_dual_layer_rag_implementation_v2_gold_star_schema, docs_deliverables_task_gld_01_kimball_star_schema_audit_and_alternatives_dual_layer_rag [EXTRACTED 1.00]
- **Pre-Deployment OWASP Security, RBAC Admin & Student UX Cleanup** — docs_deliverables_task_sec_00_pre_deployment_security_and_owasp_report_gates_g1_g8, docs_deliverables_task_sec_02_rbac_admin_api_and_portal_implementation_admin_router, docs_deliverables_task_hf_01_fe_ux_cleanup_and_root_sync_deliverable [EXTRACTED 1.00]
- **Silver v2 Deterministic Sandwich, Schema v2 (G1-G8), Explicit ZSTD Parquet & RAG Ingest** — docs_deliverables_task_slv_02_silver_schema_and_parquet_validation_doc, docs_deliverables_task_slv_03_hybrid_sandwich_and_rag_silver_implementation_doc, docs_deliverables_task_slv_04_silver_schema_v2_and_parquet_implementation_doc, docs_experiments_0001_rag_baseline_evaluation_doc [EXTRACTED 1.00]
- **ACDP Agent Governance & Prompt Execution Standards** — docs_frameworks_agent_skill_engineering_spec_doc, docs_frameworks_prompt_execution_framework_doc, docs_frameworks_team_directives_doc [EXTRACTED 1.00]
- **Cycle 06 v2 Medallion Pipeline Tasks** — docs_tasks_task_registry_task_ing_03, docs_tasks_task_registry_task_brz_02, docs_tasks_task_registry_task_slv_03, docs_tasks_task_registry_task_slv_04, docs_tasks_task_registry_task_gld_02 [INFERRED 0.95]
- **Cycle 07 Full Cloud Free-Tier Infrastructure Tasks** — docs_tasks_task_registry_task_cld_04, docs_tasks_task_registry_task_cld_05, docs_tasks_task_registry_task_cld_06, docs_tasks_task_registry_task_cld_07 [INFERRED 0.95]
- **DIR-018 In-Repo Task Synchronization Artifacts** — docs_tasks_task_registry_in_repo_task_registry, docs_tasks_task_registry_tasks_data_json, docs_tasks_task_registry_index_html, agents_skills_repo_task_manager_scripts_sync_tasks [EXTRACTED 1.00]

## Communities (161 total, 40 thin omitted)

### Community 0 - "V2 URL Discovery"
Cohesion: 0.06
Nodes (32): apply_conditional_http_checks(), build_seed_candidates(), canonicalize_url(), compute_relevance_score(), _contains_keyword(), deduplicate_and_rank(), DiscoveredCandidate, DiscoveryManifest (+24 more)

### Community 1 - "Analytics API Router"
Cohesion: 0.07
Nodes (27): get_analytics_overview(), get_analytics_seasonality(), get_competition_detail(), list_competitions(), AnalyticsDashboardDTO, DomainMetricDTO, HealthResponse, KpiOverviewDTO (+19 more)

### Community 2 - "V2 Silver Transform"
Cohesion: 0.06
Nodes (29): apply_post_llm_guards(), build_bounded_llm_markdown(), build_llm_user_prompt(), _canonical_domain(), clean_markdown_text(), _contains_tech_term(), _create_instructor_client(), DeterministicSignals (+21 more)

### Community 3 - "Ollama Validation Bridge"
Cohesion: 0.07
Nodes (19): Ollama Hardware & Model Matrix, check_cli(), check_endpoint(), main(), Ollama Bridge Skill, Academic & University Domain Whitelist, HTTP Status & Anti-Bot Technical Guide, run_all_tests() (+11 more)

### Community 4 - "JWT Auth & Seeding"
Cohesion: 0.08
Nodes (18): seed_local_users(), get_me(), login(), logout(), refresh_tokens(), register(), _set_refresh_cookie(), _to_profile() (+10 more)

### Community 5 - "Auth & Bookmarks Tests"
Cohesion: 0.06
Nodes (18): test_auth_register_login_refresh_rotation_and_reuse_detection(), test_bookmarks_idempotency_and_cross_user_isolation(), test_analytics_overview_and_seasonality_match_gold_star_schema(), test_competitions_explorer_filters_detail_and_sql_injection_safety(), test_gold_mart_ttl_cache_reduces_repeated_queries_over_95_pct(), test_health_endpoint_reports_db_and_gold_count(), FakeCvStorageService, _register_and_login() (+10 more)

### Community 6 - "Gold Star Schema"
Cohesion: 0.08
Nodes (20): build_metabase_r2_init_sql(), build_motherduck_r2_init_sql(), _competition_richness_score(), _compute_competition_total_prize_vnd(), _deduplicate_competition_payloads(), export_gold_parquet_and_sync_r2(), export_silver_parquet(), _extract_batch_sort_key() (+12 more)

### Community 7 - "Admin & DuckDB Refresh"
Cohesion: 0.09
Nodes (17): refresh_duckdb_r2_connection(), get_admin_openapi(), get_admin_swagger_docs(), get_admin_telemetry(), list_admin_users(), refresh_admin_caches(), _to_admin_user_dto(), update_admin_user() (+9 more)

### Community 8 - "Cloud Environment Config"
Cohesion: 0.05
Nodes (40): environment, ADMIN_EMAILS, BRONZE_STORAGE_BACKEND, CHAT_MODEL, CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN, CORS_ORIGIN_REGEX, CORS_ORIGINS (+32 more)

### Community 9 - "V2 Pydantic Schemas"
Cohesion: 0.12
Nodes (9): clean_placeholder(), _clean_string_list(), Competition, CompetitionExtractionResult, PrizeTier, TimelineStage, test_silver_schema_v2_gap_g1_g8_resolved(), test_silver_v2_schema_validation_and_g7_rejection() (+1 more)

### Community 10 - "Next.js Web Dependencies"
Cohesion: 0.07
Nodes (37): dependencies, lucide-react@^0.511.0, next@^16.4.0, react@^19.1.0, react-dom@^19.1.0, react-is@^19.1.0, recharts@^2.15.3, devDependencies (+29 more)

### Community 11 - "Student Profile Router"
Cohesion: 0.12
Nodes (15): User, UserProfile, _compute_completeness(), delete_my_cv_pdf(), download_student_cv_pdf(), get_my_profile(), _get_or_create_profile(), get_public_profile() (+7 more)

### Community 12 - "V1 Pydantic Schemas"
Cohesion: 0.10
Nodes (9): clean_placeholder(), Competition, CompetitionExtractionResult, PrizeTier, TimelineStage, test_clean_placeholder(), test_competition_creation_and_normalization(), test_json_roundtrip_integrity() (+1 more)

### Community 13 - "FastAPI CORS & Seeding"
Cohesion: 0.09
Nodes (4): get_db_session(), init_oltp_schema(), lifespan(), health_check()

### Community 14 - "Crawl4AI Web Crawler"
Cohesion: 0.10
Nodes (11): crawl_urls_to_bronze(), _load_urls_from_r2_discovery(), main(), _merge_unique_urls(), package_bronze_html(), _parse_args(), _resolve_embedding_provider(), _resolve_query_provider() (+3 more)

### Community 15 - "RAG Chat Router"
Cohesion: 0.14
Nodes (14): ChatMessage, ChatSession, delete_chat_session(), _handle_rag_chat(), list_chat_sessions(), list_session_messages(), rag_chat(), rag_query_alias() (+6 more)

### Community 16 - "Bronze Storage Evaluation"
Cohesion: 0.07
Nodes (26): Planned ADR-0003 (Bronze Storage & Table Format), Apache Hudi (Rejected, JVM/Spark Dependent), Apache Iceberg (pyiceberg), ACDP Bronze Layer, Cloudflare R2 (Zero Egress Fees), Crawl4AI + Playwright Web Crawler, Data Swamp Risk, Delta Lake (delta-rs / deltalake 0.25+ & delta-kernel-rs) (+18 more)

### Community 17 - "Dual-Layer RAG Retrieval"
Cohesion: 0.13
Nodes (14): docs/experiments/data/0001-golden-queries.jsonl, RetrievalConfig, retrieve_contexts(), _build_ragas_evaluators(), load_golden_dataset(), main(), _parse_args(), _percentile() (+6 more)

### Community 18 - "PostgreSQL OLTP Models"
Cohesion: 0.12
Nodes (8): SavedCompetition, UserSession, utc_now(), delete_bookmark(), list_bookmarks(), save_bookmark(), BookmarkCreateRequest, BookmarkDTO

### Community 19 - "Web App Layout & Fonts"
Cohesion: 0.12
Nodes (20): beVietnam, jakarta, jetbrainsMono, metadata, RootLayout(), LogoFull(), LogoMark(), LogoMonochrome() (+12 more)

### Community 20 - "RFC-0001 & BI Boundary"
Cohesion: 0.07
Nodes (21): PercentileSemanticChunker (Pure Python, 0 DeprecationWarnings), Qdrant v1.20.2 & PG 17+/18.7 Compatibility, RFC-0001 Implementation Report (TASK-QA-01), Offline Unit Tests (61/61 Passed) & Zero Doc Drift (116 Files), Tier 3: Metabase Docker (--profile bi, On-Demand Local Only, 0 MB Default), Tier 2: MotherDuck Lite Free (Cloud DataOps SQL Workbench, $0/mo), TASK-CLD-02 Visual Dossier (HTML), Tier 1: Web /dashboard (Next.js 16 + Recharts on 6 mart_* Tables) (+13 more)

### Community 21 - "Admin UI & API Client"
Cohesion: 0.09
Nodes (23): OpenApiPreview, RateLimitBlockEvent, AdminCacheRefreshDTO, AdminCacheRefreshRequest, AdminTelemetryDTO, AdminUserDTO, AdminUsersSummaryDTO, AdminUserUpdateRequest (+15 more)

### Community 22 - "Web Portal Pages"
Cohesion: 0.14
Nodes (21): AdminPage(), BookmarksPage(), LoginPage(), formatBytes(), HCMUTE_MAJORS, ProfilePage(), ProfileWorkspace(), SUGGESTED_ROLES (+13 more)

### Community 23 - "V1 Gold Analytics"
Cohesion: 0.10
Nodes (12): _register_organizer(), build_metabase_r2_init_sql(), classify_organizer_tier(), classify_team_profile(), compute_competition_key(), _compute_competition_total_prize_vnd(), export_silver_parquet(), normalize_canonical_url() (+4 more)

### Community 24 - "AppSettings & R2 Config"
Cohesion: 0.10
Nodes (4): AppConfig, test_g2_fail_fast_jwt_secret_validation_in_production(), test_storage_options_cloudflare_r2_backend(), test_storage_options_custom_s3_backend_http()

### Community 25 - "RAG Service & Fallback"
Cohesion: 0.11
Nodes (12): answer_with_contexts(), _build_openai_messages(), check_qdrant_health(), _fallback_duckdb_gold_search(), _generate_answer_with_fallback(), _generate_with_litellm_router(), _generate_with_openai_compatible(), _get_backup_qdrant() (+4 more)

### Community 26 - "Cloud Ops & R2 Client"
Cohesion: 0.16
Nodes (8): _async_keep_alive_and_check_supabase(), check_r2_gold_data_quality(), format_markdown_summary(), keep_alive_and_check_qdrant(), keep_alive_and_check_supabase(), main(), ping_serving_api(), run_oltp_pg_dump_backup()

### Community 27 - "AI Slop Linter"
Cohesion: 0.17
Nodes (6): AuditReport, main(), print_text_report(), SlopDetector, SlopViolation, TestSlopDetector

### Community 28 - "Doc Drift Auditor"
Cohesion: 0.24
Nodes (17): AuditFinding, check_canonical_fact_drift(), check_directive_sync(), check_internal_markdown_links(), check_skill_registry_parity(), _classify_tier(), compute_blast_radius(), discover_skills() (+9 more)

### Community 29 - "Two-Tier Gold & RAG"
Cohesion: 0.09
Nodes (20): TASK-GLD-01: Kimball Star Schema Audit & Alternatives, Dual-Layer RAG (Silver Text + Gold Metadata), Two-Tier Gold Architecture (Kimball Core + OBT Marts), TASK-GLD-01 Visual Dossier (HTML), TASK-GLD-02: Two-Tier Gold & Dual-Layer RAG Implementation, v2/gold_star_schema.py (Two-Tier Gold Builder), TASK-GLD-02 Visual Dossier (HTML), TASK-ING-01: Search Pattern & Free-Tier Crawling Study (+12 more)

### Community 30 - "V2 Silver Transform Tests"
Cohesion: 0.09
Nodes (6): InMemoryR2Client, test_deterministic_extraction_jsonld_og_official_links_and_regex(), test_dir022_scope_gate_and_media_partner_dedup(), test_end_to_end_silver_transform_and_rag_ingest_from_silver(), test_post_llm_guards_enforce_canonical_url(), test_split_bronze_pages_and_in_ram_clean_markdown()

### Community 31 - "Gold Star Schema Tests"
Cohesion: 0.09
Nodes (8): test_currency_normalization_edge_cases(), test_date_resolution_and_academic_terms(), test_expired_open_status_normalizes_to_closed(), test_fee_and_team_and_domain_classification(), test_load_silver_prefers_newest_batch_and_deduplicates(), test_motherduck_cli_sql_output(), test_r2_end_to_end_silver_to_gold_zero_local_disk(), test_star_schema_bridge_allocation_and_edge_cases()

### Community 32 - "Competition Cards & Detail"
Cohesion: 0.16
Nodes (14): CompetitionCardProps, CompetitionDetailPage(), dynamic, extractHost(), metadata, dynamic, HomePage(), QUICK_FILTERS (+6 more)

### Community 33 - "Analytics Dashboard Page"
Cohesion: 0.25
Nodes (15): DashboardPage(), dynamic, metadata, ChartCard(), ChartCardProps, DomainBarChart(), MODE_COLORS, ModeDonutChart() (+7 more)

### Community 34 - "Security Middleware Exports"
Cohesion: 0.13
Nodes (7): apply_security_headers(), enforce_ai_rate_limit(), extract_client_ip(), _masked_internal_error_response(), register_security_exception_handlers(), _unhandled_exception_handler(), SecurityHardeningMiddleware

### Community 36 - "Qdrant Vector Store"
Cohesion: 0.13
Nodes (8): build_chunker(), chunk_single_document(), clean_markdown(), ensure_collection(), get_vector_store(), ingest(), list_latest_bronze_snapshots(), load_competition_documents()

### Community 37 - "OWASP Security Tests"
Cohesion: 0.17
Nodes (8): reset_rate_limiter(), _register_and_login(), test_g3_rag_chat_and_query_require_authentication(), test_g4_ai_rate_limiting_per_user_day_and_global_rpm(), test_g4_auth_and_public_rate_limiting_per_ip(), test_g5_hide_public_docs_and_protect_admin_docs(), test_g6_admin_rbac_kill_switch_and_cache_refresh(), test_g7_security_headers_and_global_exception_masking()

### Community 38 - "Gold Dimension Builders"
Cohesion: 0.10
Nodes (11): build_gold_star_schema(), _register_organizer(), classify_competition_domains(), classify_organizer_tier(), classify_team_profile(), _create_data_marts(), _create_star_schema_ddl(), is_participation_free() (+3 more)

### Community 39 - "SWOT & Slide Validators"
Cohesion: 0.16
Nodes (7): main(), validate_benchmark(), main(), validate_slides(), compute_scorecard(), main(), main()

### Community 40 - "V1 LLM Extraction"
Cohesion: 0.15
Nodes (7): clean_markdown_content(), extract_competition_from_markdown(), parse_bronze_key(), process_bronze_bucket(), upload_to_silver(), classify_competition_domains(), is_participation_free()

### Community 41 - "Gold Metadata Pre-Filtering"
Cohesion: 0.13
Nodes (11): build_gold_filter(), _get_embeddings(), infer_gold_filters(), _query_qdrant_with_fallback(), _retrieve_context_points(), test_build_gold_filter_constructs_qdrant_must_conditions(), test_infer_gold_filters_extracts_structured_intents(), test_percentile_semantic_chunker_splits_on_topic_shift_without_deprecation() (+3 more)

### Community 42 - "TypeScript Compiler Config"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 43 - "TLCN Thesis Report"
Cohesion: 0.13
Nodes (19): BronzeRecord Schema, Four Student Competition Bottlenecks, Gold Dimensional Data Marts, Modular Hybrid RAG & Ragas Evaluation, 4-Layer Lean Medallion Lakehouse Architecture, Báo cáo Tiểu luận Chuyên ngành KTDL, 7 Sample Competitions Bronze Benchmark, SilverCompetitionRecord Schema (+11 more)

### Community 44 - "Academic Term & Date Keys"
Cohesion: 0.13
Nodes (6): _register_date(), map_academic_term(), resolve_date_sk(), resolve_effective_registration_status(), compute_competition_key(), parse_date_value()

### Community 45 - "Gold DDL & R2 Sync"
Cohesion: 0.14
Nodes (9): build_gold_star_schema(), _register_date(), _create_data_marts_and_aliases(), _create_star_schema_ddl(), export_gold_parquet_and_sync_r2(), map_academic_term(), normalize_mode(), parse_date_value() (+1 more)

### Community 47 - "Silver Progress Presentation"
Cohesion: 0.11
Nodes (14): Bronze Delta Lake (delta-rs + Zstd L3), Báo Cáo Tiến Độ Lớp Bạc (Silver Layer) Presentation, generate_fingerprint() Deduplication, Lean Medallion Lakehouse Architecture, SilverCompetitionRecord (11 Core Fields, Pydantic v2), Zstandard L3 Compression Benchmark (80.2% Savings), src/acdp/1_crawl_to_bronze.py (upload_to_bronze), src/acdp/2_instruction.py (push_silver_records_to_r2) (+6 more)

### Community 48 - "Hybrid Sandwich & Ragas"
Cohesion: 0.12
Nodes (16): TASK-SLV-03: Hybrid Deterministic Sandwich & Silver RAG Implementation, 4-Step Hybrid Deterministic Sandwich (Extract, Scope Gate DIR-022, Bounded Instructor LLM, Validate & Load), Silver-to-Qdrant RAG Ingest (26 Clean Markdown -> 648 bge-m3 Chunks), TASK-SLV-03 Visual Dossier (HTML), EXP-0001: Dual-Layer RAG (v2) Baseline Evaluation Protocol (Ragas), Dual-Layer RAG (Silver Markdown bge-m3 + Gold OBT Metadata Pre-Filtering + gemini-3.5-flash-lite), ACDP Empirical Experiments & Benchmarking Hub, TEAM_DIRECTIVES.md: Single Source of Truth Team Directives & Memory Ledger (DIR-001 to DIR-024) (+8 more)

### Community 49 - "Prefect Medallion Flow"
Cohesion: 0.18
Nodes (6): _list_r2_keys(), medallion_lakehouse_flow(), task_build_gold_r2(), task_extract_silver(), task_ingest_bronze(), task_ingest_qdrant()

### Community 50 - "Cloudflare BGE-M3 Embedder"
Cohesion: 0.14
Nodes (5): CloudflareBgeM3Embedder, _embed_with_fastembed_fallback(), _is_recoverable_rate_or_server_error(), RagUnavailableError, test_cloudflare_bge_m3_rag_pipeline_and_config()

### Community 51 - "In-Repo Task Sync"
Cohesion: 0.22
Nodes (8): Task Schema Specification, embed_json_in_html(), load_tasks_data(), main(), render_task_registry_md(), validate_tasks_data(), TestSyncTasks, Repo Task Manager Skill

### Community 52 - "R2 & Backup Env Vars"
Cohesion: 0.17
Nodes (17): AWS_ACCESS_KEY_ID, AWS_ENDPOINT_URL, AWS_REGION, AWS_SECRET_ACCESS_KEY, BUCKET_NAME, OLTP_BACKUP_R2_PREFIX, OLTP_BACKUP_RETENTION_DAYS, POSTGRES_MODE (+9 more)

### Community 53 - "RAG & OpenAPI Tests"
Cohesion: 0.12
Nodes (5): get_rag_cache_stats(), test_openapi_31_contract_is_valid(), test_rag_chat_persistence_ungrounded_and_outage(), test_rag_litellm_router_fallback_mode(), test_rag_llm_fallback_chain_and_ttl_cache()

### Community 54 - "QA Tech Decision Tests"
Cohesion: 0.12
Nodes (6): test_config_r2_exclusive_and_llm_guardrails(), test_deliverable_covers_all_eight_decisions_and_seven_core_components(), test_dir024_and_standard_delivery_gate_synced(), test_docker_compose_zero_latest_and_ram_budget(), test_keep_alive_workflow_daily_and_weekly_backup(), test_rfcs_exist_with_valid_lifecycle_status()

### Community 55 - "V2 RAG Ingestion"
Cohesion: 0.20
Nodes (8): build_chunker(), enrich_document_with_gold_metadata(), ingest(), list_latest_silver_markdown_snapshots(), load_competition_documents_from_silver(), load_silver_extraction_index(), main(), _parse_args()

### Community 56 - "Academic Research Skill"
Cohesion: 0.14
Nodes (11): Academic Researcher Skill, 4-Step Scientific Execution Protocol, Information Extraction, Lakehouse Architectures, docs/academic/literature-review.md, Retrieval-Augmented Generation (RAG), docs/academic/references.bib, examples/sample_sota_matrix.md (+3 more)

### Community 57 - "Delivery Gate Validator"
Cohesion: 0.19
Nodes (3): _extract_section(), validate_delivery_package(), TestStandardDeliveryGate

### Community 58 - "DuckDB R2 Client"
Cohesion: 0.16
Nodes (5): get_duckdb_conn(), _get_or_init_shared_connection(), _hydrate_gold_entities_from_r2(), reset_duckdb_connection(), get_duckdb()

### Community 60 - "FastAPI Auth Dependencies"
Cohesion: 0.17
Nodes (5): get_current_user(), get_optional_user(), require_admin(), require_lecturer_or_admin(), _sync_admin_role_if_listed()

### Community 61 - "OpenAPI Schema Exporter"
Cohesion: 0.14
Nodes (5): export_openapi_schema(), test_admin_frontend_security_and_swagger_route(), test_frontend_use_case_ux_enhancements(), test_public_frontend_has_no_internal_tech_or_method_jargon(), test_root_openapi_env_compose_and_readme_are_synced()

### Community 62 - "Silver R2 Payload Loader"
Cohesion: 0.16
Nodes (7): _competition_richness_score(), _deduplicate_competition_payloads(), _extract_batch_sort_key(), load_silver_competitions(), load_silver_competitions_from_r2(), load_silver_competitions_with_source(), parse_silver_key()

### Community 63 - "Docker Compose Services"
Cohesion: 0.13
Nodes (14): container_name, image, ports, profiles, restart, user, volumes, services (+6 more)

### Community 64 - "Cloudflare Workers Embeddings"
Cohesion: 0.17
Nodes (3): CloudflareWorkersAIEmbeddings, EmbeddingRateLimitError, _is_rate_limit_error()

### Community 65 - "Doc Drift Audit Tests"
Cohesion: 0.35
Nodes (5): load_rules(), run_full_audit(), _create_clean_fixture_repo(), TestAuditDocDrift, _write()

### Community 66 - "Competitions Explorer Page"
Cohesion: 0.18
Nodes (12): CompetitionsPage(), dynamic, FILTER_LABELS, metadata, VALUE_LABELS, DOMAIN_OPTIONS, FilterForm(), FilterSidebar() (+4 more)

### Community 67 - "Copilot Workspace Page"
Cohesion: 0.20
Nodes (12): buildCompetitionScopes(), CopilotPage(), dynamic, metadata, CompetitionScopeOption, CopilotWorkspace(), SAMPLE_PROMPTS, UiMessage (+4 more)

### Community 68 - "Web & Gold Stack R&D"
Cohesion: 0.27
Nodes (11): Dual-Engine Storage Separation (OLTP vs OLAP vs Vector), 3-Tier Analytics & BI Boundary, SPEC-0001: System Foundation & Lean Configuration, SPEC-0002: Lean Data Ingestion & Bronze-to-Silver Extraction, SPEC-0003: Gold Layer Kimball Star Schema & Data Marts, Two-Tier Gold Kimball Star Schema (9 Core + 6 Marts), SPEC-0004: FastAPI Serving Gateway, PostgreSQL OLTP & OpenAPI Contract, PostgreSQL 17+/18 OLTP Schema (6 Tables) (+3 more)

### Community 69 - "Profile Request Validation"
Cohesion: 0.29
Nodes (4): _clean_optional_str(), _normalize_tag_list(), ProfileUpdateRequest, _validate_https_url()

### Community 71 - "Docker & Infra Tests"
Cohesion: 0.18
Nodes (4): _parse_mem_mb(), test_docker_compose_version_pinning_and_profiles(), test_dockerignore_and_dockerfile_api_hardening(), test_keep_alive_workflow_pg_dump_url_and_backup()

### Community 72 - "Workers AI Embeddings Dup"
Cohesion: 0.19
Nodes (3): CloudflareWorkersAIEmbeddings, EmbeddingRateLimitError, _is_rate_limit_error()

### Community 73 - "Silver Schema Unit Tests"
Cohesion: 0.14
Nodes (6): test_competition_extraction_result_coercion(), test_competition_extraction_result_container(), test_empty_document_handling(), test_prize_tier_validation(), test_silver_v2_explicit_pyarrow_zstd_and_timeline_stages(), test_timeline_stage_validation()

### Community 74 - "Anti-Slop Scientific Skill"
Cohesion: 0.18
Nodes (13): detect_ai_slop.py Deterministic Linter, anti-slop-scientific-writer Skill, Hybrid Retrieval Architecture Specification Example, DuckDB vs SQLite Parquet Comparison Example, Catalog of 25 AI Structural Tropes & Anti-Patterns, Scientific Writing & Technical Documentation Style Guide, Banned AI Vocabulary & Scientific Alternatives Lexicon, doc-decision-sync Skill (+5 more)

### Community 75 - "Docker Build & Profiles"
Cohesion: 0.17
Nodes (13): build, container_name, depends_on, extra_hosts, ports, profiles, restart, context (+5 more)

### Community 76 - "Web Container Env Config"
Cohesion: 0.15
Nodes (13): condition, api, INTERNAL_API_URL, NEXT_PUBLIC_API_URL, NODE_OPTIONS, web, container_name, depends_on (+5 more)

### Community 78 - "V2 Discovery Unit Tests"
Cohesion: 0.18
Nodes (7): test_deduplication_and_http_304_check(), head_handler(), _run_head(), test_tier2_budget_cap_and_serper_fallback(), handler(), _run(), test_upload_manifest_to_r2()

### Community 79 - "Postgres Container Env"
Cohesion: 0.17
Nodes (12): POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, command, container_name, environment, image, ports (+4 more)

### Community 80 - "Visual Dossier & Delivery"
Cohesion: 0.20
Nodes (6): Sample Manual Test & Advisor Demo Runbook, Standard Delivery Gate Skill, ACDP Visual Dossier HTML Template, main(), validate_report(), Visual Dossier Reporter Skill

### Community 81 - "Thesis Formatting Validator"
Cohesion: 0.20
Nodes (8): ACDP 4-Tier System Architecture Sample, FIT-HCMUTE Thesis & TLCN Guideline, check_formatting(), main(), Thesis Writer Skill, Bug Report Issue Template, Feature Request Issue Template, Pull Request Template

### Community 82 - "Prefect Container Config"
Cohesion: 0.18
Nodes (11): PREFECT_SERVER_API_HOST, PREFECT_UI_API_URL, command, container_name, environment, image, ports, profiles (+3 more)

### Community 83 - "Architecture Diagram Core"
Cohesion: 0.22
Nodes (11): Bronze Layer (n post, plain text), Chatbot (VectorRAG, GraphRAG), Competition Sources (Eureka, ICPC, Hackathon, CTF, Mastering IT, AI Challenge), Dashboard, Gold Layer (metrics), Graph RAG, Serving Layer, Silver Layer (list, metadata, vector matrix) (+3 more)

### Community 84 - "GitHub Actions Steps"
Cohesion: 0.24
Nodes (11): steps, name, run, uses, with, steps, enable-cache, if-no-files-found (+3 more)

### Community 86 - "Weekly pg_dump Workflow"
Cohesion: 0.20
Nodes (10): run_pg_dump, on, schedule, workflow_dispatch, default, description, required, type (+2 more)

### Community 87 - "Adaptive Crawler Patches"
Cohesion: 0.20
Nodes (5): _attach_crawler_patches(), _resilient_map_query_semantic_space(), _extract_query_list(), main(), upload_to_bronze()

### Community 88 - "BM25 Hybrid Retriever"
Cohesion: 0.33
Nodes (4): RetrievedChunk, BM25CorpusRetriever, _tokenize_bm25(), test_bm25_corpus_retriever_ranks_relevant_chunk_first()

### Community 89 - "Container Resource Limits"
Cohesion: 0.22
Nodes (9): deploy, resources, cpus, memory, deploy, deploy, deploy, deploy (+1 more)

### Community 90 - "Metabase Container Env"
Cohesion: 0.22
Nodes (9): AWS_ACCESS_KEY_ID, AWS_ENDPOINT_URL, AWS_REGION, AWS_SECRET_ACCESS_KEY, BUCKET_NAME, JAVA_TOOL_OPTIONS, MB_ANON_TRACKING_ENABLED, MB_DB_FILE (+1 more)

### Community 91 - "Qdrant Container Config"
Cohesion: 0.22
Nodes (9): QDRANT__STORAGE__PERFORMANCE__MAX_SEARCH_THREADS, container_name, environment, image, ports, profiles, restart, volumes (+1 more)

### Community 92 - "Medallion Layer Deliverables"
Cohesion: 0.22
Nodes (9): Bronze Layer, Gold Layer, Silver Layer, NT-012: Dual-Layer RAG (v2) & Ragas Baseline Scorecard, NT-024: Gold Layer Kimball Star Schema & Analytical Data Marts Design, TASK-BRZ-02: Raw Rendered HTML Bronze Implementation (v2/bronze_crawl.py), TASK-GLD-02: Two-Tier Gold (A1-A4) & Dual-Layer RAG Metadata Ingestion, TASK-SLV-03: Hybrid Deterministic Sandwich & Clean Markdown Silver Implementation (+1 more)

### Community 93 - "Keep-Alive & DQ Workflow"
Cohesion: 0.22
Nodes (8): jobs, keep-alive-and-dq-audit, name, runs-on, timeout-minutes, name, permissions, contents

### Community 94 - "RAG Response TTL Cache"
Cohesion: 0.28
Nodes (3): RagResponseTTLCache, RagResult, _sync_query_rag()

### Community 95 - "Bronze Purity & R2 Audit"
Cohesion: 0.22
Nodes (8): R2 Bucket Audit Baseline (83 Objects, 2.26 MB), Immutable Raw Rendered HTML in Bronze (s3://acdp-lakehouse/bronze/), DefaultMarkdownGenerator in Silver RAM (0 ms Browser Overhead), TASK-BRZ-01 Visual Dossier (HTML), TASK-BRZ-02 Raw Rendered HTML Bronze Implementation (v2/bronze_crawl.py), Live R2 Bronze Batch Benchmark (33/36 URLs, 93 Pages, 16.264 MB), package_bronze_html() & ACDP_PAGE_BOUNDARY, TASK-BRZ-02 Visual Dossier (HTML)

### Community 96 - "Full Cloud Stack Summary"
Cohesion: 0.25
Nodes (8): DIR-016 Web & OLTP/OLAP Split Stack, Bronze Layer (Raw Rendered HTML on Cloudflare R2), Cloud Ops & Weekly pg_dump Backups (GitHub Actions), Dual-Layer RAG & Ragas Evaluation (Qdrant + bge-m3 + Gemini 3.5 Flash Lite), Gold Layer (Two-Tier Kimball Star Schema & DuckDB httpfs), Serving & Web Portal (FastAPI + PostgreSQL 18 + Next.js 16), Silver Layer (Hybrid Deterministic Sandwich & Pydantic/Arrow Schema), 3-Tier Discovery (Sitemap/RSS/GDELT + Search APIs + ETag)

### Community 97 - "ADR-0002 Free-Tier Cloud"
Cohesion: 0.25
Nodes (3): 100% Cloud Free-Tier Stack Matrix, Keep-Alive Automation, Backup & Demo Day Protocol, 3-Tier BI Architecture & MotherDuck Lite

### Community 98 - "Security Gates & HF-01"
Cohesion: 0.25
Nodes (7): TASK-HF-01: Frontend UX Cleanup & Root Docs Sync, TASK-HF-01 Visual Dossier (HTML), TASK-SEC-00: Pre-Deployment Security & OWASP Blueprint, TASK-SEC-00 Visual Dossier (HTML), src/acdp/api/routers/admin.py & SecurityHardeningMiddleware, TASK-SEC-02: RBAC, Admin API & /admin Portal, TASK-SEC-02 Visual Dossier (HTML)

### Community 99 - "Literature & SOTA Matrix"
Cohesion: 0.29
Nodes (7): Armbrust et al. (2021) Medallion Lakehouse, Gao et al. (2023) Modular RAG Survey, Lappas et al. (2009) Expert Team Formation, Lewis et al. (2020) DPR RAG, Sample Literature Review & SOTA Matrix, Xu et al. (2024) LLM Web Extraction, SOTA Academic Venues & Search Protocols

### Community 100 - "Frontend Design Validator"
Cohesion: 0.33
Nodes (4): ACDP Design Tokens, main(), validate_component(), Frontend Designer Skill

### Community 101 - "Container Healthchecks"
Cohesion: 0.57
Nodes (7): healthcheck, interval, retries, test, timeout, healthcheck, healthcheck

### Community 102 - "TLCN Proposal & Scope"
Cohesion: 0.29
Nodes (7): Bảng đăng ký Đề tài Tiểu luận Chuyên ngành, Master Specification & Initialization Prompt, ACDP Direction & AI Prompting Guide, Phase 1 TLCN Lean MVP Scope, Phase 2 KLTN Full-Scale Scope, ACDP Documentation Portal, Spec-Driven Development Protocol

### Community 103 - "VectorRAG & GraphRAG"
Cohesion: 0.29
Nodes (7): Chunking, Embedding, Knowledge Graph, LLM, LLM / GLiNER, Ontology / Triples, VectorDB

### Community 104 - "Silver Schema v2 Gaps"
Cohesion: 0.29
Nodes (6): Vietnam Dedicated Competition Landing Pages Expansion Report (15 Verified URLs), TASK-SLV-02: Silver Schema & Parquet Validation Audit, Normalized Silver Parquet Tables (competitions, prizes, timeline_stages) with Explicit PyArrow Schema, TASK-SLV-04: Silver Schema v2 (G1-G8) & PyArrow Explicit ZSTD Parquet, R2 Silver ZSTD Parquet Outputs (competitions 24x43, prizes 90x10, timeline_stages 89x9), TASK-SLV-04 Visual Dossier (HTML)

### Community 105 - "Ragas 3-System Ablation"
Cohesion: 0.29
Nodes (6): src/acdp/config.py (Groq qwen3.8-27b & OpenRouter gemma-4-31b), src/acdp/api/services/rag_service.py (Gold OBT Pre-Filtering), NT-012 Dual-Layer RAG & Ragas Harness Visual Dossier, EXP-0001 3-System RAG Ablation (Naive Dense, BM25, Dual-Layer), Qdrant Cloud Vector Index (acdp_competitions_bge_m3, 778 points), EXP-0001 Ragas Target Scorecard

### Community 106 - "Feasibility & T01 Review"
Cohesion: 0.29
Nodes (5): NT-013 Business & Technical Feasibility Review (T01 Review), Hybrid Ingestion & Silver Entity Resolution, Seed Knowledge First & Aspect-Based Sentiment Analysis (ABSA), docs/rd-tasks/T01.md, Unstructured-to-Structured ELT (5 OLAP Dimensions)

### Community 107 - "Competition Landscape Survey"
Cohesion: 0.29
Nodes (6): 8-Dimension Survey Matrix of 18 Student Competitions, 4 Student Bottlenecks & ACDP Technical Countermeasures, Academic Grounding (Cho & Garcia-Molina, Chakrabarti, West & Dragut), NT-014 Academic Competition Landscape Survey & Adaptive Ingestion, 4-Pillar Adaptive Ingestion Architecture, 4-Stage Geographic Expansion Roadmap

### Community 108 - "Query Space Mapping"
Cohesion: 0.29
Nodes (3): _attach_crawler_patches(), _resilient_map_query_semantic_space(), _extract_query_list()

### Community 110 - "Agent Operating Contracts"
Cohesion: 0.33
Nodes (6): AGENTS.md Universal AI Agent Operating Contract, Progressive Disclosure Skill Loading, ACDP Agent Skills Suite & Engineering Standards, 3-Tier Skill Architecture (Discovery, Activation, Execution), CLAUDE.md Claude Code Configuration & Standing Brief, GEMINI.md Antigravity & Gemini CLI Workspace Rules

### Community 111 - "Web Sprint 02 Deliverables"
Cohesion: 0.33
Nodes (6): Serving & Web Layer, NT-025: FastAPI Serving Gateway & PostgreSQL 18 OLTP, NT-029: Web Sprint 02 Full-Stack Implementation, TASK-HF-01: Frontend UX Cleanup & Root Docs Sync, TASK-SEC-02: RBAC (Admin/Lecturer/Student), Admin API & /admin Portal, TASK-SRV-01: Student Mini-CV Profile Page (/profile)

### Community 113 - "R2 Gold Pipeline Verify"
Cohesion: 0.33
Nodes (3): run_gold_pipeline(), verify_analytics(), verify_analytics_from_r2()

### Community 114 - "Deliverable Template & Runbook"
Cohesion: 0.40
Nodes (3): Manual Test, CLI Deployment & Advisor Demo Runbook, 7-Section Deliverable Template Structure, docs/tasks/task-registry.md

### Community 115 - "Local Dev & Admin Docs"
Cohesion: 0.40
Nodes (4): Protected Admin Swagger UI (/api/v1/admin/docs), Local (.env.dev) vs Production Environment Separation, React Error #31 Fix (apps/web/lib/api-client.ts), scripts/seed_local_users.py (@acdp.dev Accounts)

### Community 116 - "Specs & Sprint Planning"
Cohesion: 0.40
Nodes (5): SPEC Template (0000-spec-template.md), Active Sprint & Context Memory, In-Repo Task & Deliverables Portal (index.html), ACDP 15-Week TLCN Implementation Roadmap, Web Sprint 01 Research, Architecture & Testing Plan

### Community 117 - "Cloud & Infra Deliverables"
Cohesion: 0.40
Nodes (5): Cloud & Infra Layer, TASK-CLD-04: Supabase OLTP & DuckDB Direct-on-R2 (s3://), TASK-CLD-05: Cloud Serving API & Vercel Hobby TTL Cache, TASK-CLD-06: GitHub Actions Keep-Alive, pg_dump Backup & LLM/Vector Fallback, TASK-SEC-01: OWASP Top 10 (2025/2026) Hardening & AI Quota Protection

### Community 118 - "Workflow Input Parameters"
Cohesion: 0.40
Nodes (5): public_api_url, default, description, required, type

### Community 119 - "Weekly Backup Job Config"
Cohesion: 0.40
Nodes (5): weekly-oltp-pg-dump-backup, if, name, runs-on, timeout-minutes

### Community 121 - "Vercel Proxy & TTL Cache"
Cohesion: 0.40
Nodes (5): Dockerfile.api Low-Footprint (UID 1000, PORT=7860, DUCKDB_MEMORY_LIMIT=256MB), GoldMartsTTLCache (TTL=600s, 98.27% Hit Rate, 0.34 ms Overview), TASK-CLD-05 Cloud Serving API, Vercel Proxy & GoldMartsTTLCache, Vercel Hobby Same-Origin Proxy (next.config.ts rewrites() for HttpOnly Cookies), TASK-CLD-05 Visual Dossier (HTML)

### Community 122 - "Gemini Workspace Directives"
Cohesion: 0.50
Nodes (4): 4 Adaptive Execution Pathways (Pathway A/B/C/D), DIR-018 In-Repo Task & Deliverables Management, DIR-024 7-Pillar Standard Delivery & Demo-Ready Gate, GEMINI.md Antigravity-Specific Operational Directives

### Community 123 - "V2 Medallion Topology"
Cohesion: 0.50
Nodes (4): DIR-022 Student Tech Scope, Official Site Resolution & v2 Pipeline, ACDP: Academic Competition Discovery Platform, Cloud-Native Full-Stack Topology (ADR-0002), Medallion Pipeline (v2) Architecture

### Community 125 - "Skill & Prompt Frameworks"
Cohesion: 0.50
Nodes (4): ACDP AI Agent Skill Engineering & Optimization Specification, 6 Invariant Skill Rules (3-Tier Progressive Disclosure, Negative Triggers, Determinism vs Reasoning, Externalized References, Eval Gate, Anti-Duplication), ACDP Unified Multi-Agent Prompt Execution Framework (A-PEF), 4 Adaptive Execution Pathways (Pathway A Full DSRM, B Rapid Prototyping, C Direct Q&A, D Disambiguation)

### Community 126 - "DIR-018 Task Registry"
Cohesion: 0.50
Nodes (4): DIR-018 (In-Repo Task Management), In-Repo Task Registry & Deliverables Ledger, Interactive Task Portal (index.html), tasks-data.json

### Community 127 - "Academic & Ops Layer"
Cohesion: 0.50
Nodes (4): Academic & Ops Layer, RFC-0001: Spec v2 and Cloud Parity Realignment, RFC-0002: KLTN Scale Evolution Triggers, TASK-QA-01: Tech Decision Theory x Practice x Scope Audit

### Community 129 - "Qdrant Failover & RAM"
Cohesion: 0.50
Nodes (3): Core Profile RAM Budget (1,408 MB, -26.7% vs 1,920 MB), Qdrant Failover Rebuild from R2 (RTO < 60s via acdp.v2.rag_ingest), TASK-CLD-01 Visual Dossier (HTML)

### Community 130 - "Competitor Benchmark Skill"
Cohesion: 1.00
Nodes (3): competitor-benchmark Skill, UVP Differentiation Matrix, Competitor Profiles & Landscape Teardowns

### Community 132 - "Student Mini-CV Profile"
Cohesion: 0.67
Nodes (3): TASK-SRV-01: Student Mini-CV Profile (/profile) & R2 PDF CV Storage, PostgreSQL OLTP user_profiles Table & Dual CV Support (https:// URL + R2 PDF <= 2MB), TASK-SRV-01 Visual Dossier (HTML)

## Knowledge Gaps
- **220 isolated node(s):** `acdp`, `4 Adaptive Execution Pathways (Pathway A/B/C/D)`, `Universal Guardrails`, `DIR-011 Tabula Rasa in Tech Research & Peer Defense`, `DIR-012 Temporal Grounding (September 2026)` (+215 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1065 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **40 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `Student Profile Router` to `Security Middleware Exports`, `JWT Auth & Seeding`, `Admin & DuckDB Refresh`, `OWASP Security Middleware`, `FastAPI CORS & Seeding`, `RAG Chat Router`, `PostgreSQL OLTP Models`, `FastAPI Auth Dependencies`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Are the 36 inferred relationships involving `User` (e.g. with `get_current_user()` and `get_optional_user()`) actually correct?**
  _`User` has 36 INFERRED edges - model-reasoned connections that need verification._
- **What connects `acdp`, `4 Adaptive Execution Pathways (Pathway A/B/C/D)`, `Universal Guardrails` to the rest of the system?**
  _220 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `V2 URL Discovery` be split into smaller, more focused modules?**
  _Cohesion score 0.06151062867480778 - nodes in this community are weakly interconnected._
- **Why does `AppConfig` connect `AppSettings & R2 Config` to `Auth & Bookmarks Tests`, `LLM & Qdrant Settings`, `Docker & Infra Tests`, `OWASP Security Middleware`, `FastAPI CORS & Seeding`, `Asyncpg & Supabase Engine`, `Cloudflare BGE-M3 Embedder`, `RAG & OpenAPI Tests`, `QA Tech Decision Tests`, `RAG Service & Fallback`, `Cloud Ops & R2 Client`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Are the 18 inferred relationships involving `AppConfig` (e.g. with `build_async_engine()` and `_async_keep_alive_and_check_supabase()`) actually correct?**
  _`AppConfig` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Should `Analytics API Router` be split into smaller, more focused modules?**
  _Cohesion score 0.06713286713286713 - nodes in this community are weakly interconnected._