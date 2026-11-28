# Graph Report - acdp-platform  (2026-11-28)

## Corpus Check
- 268 files · ~378,813 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: (none) 6, .example 1, .api 1)

## Summary
- 2810 nodes · 5605 edges · 171 communities (139 shown, 32 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 317 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ade49503`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- discovery.py
- Analytics API Router
- silver_transform.py
- Ollama Validation Bridge
- JWT Auth & Seeding
- data_contracts.py
- gold_star_schema.py
- Admin & DuckDB Refresh
- Cloud Environment Config
- V2 Pydantic Schemas
- Next.js Web Dependencies
- Student Profile Router
- Deliverable: Entity Resolution & Khử trùng Cuộc thi Đa nguồn, Đa mùa giải (`TASK-DQ-04`)
- main.py
- bronze_crawl.py
- RAG Chat Router
- Bronze Storage Evaluation
- rag_eval.py
- PostgreSQL OLTP Models
- Web App Layout & Fonts
- RFC-0001 & BI Boundary
- Admin UI & API Client
- Web Portal Pages
- build_gold_star_schema
- cloud_ops.py
- rag_service.py
- build_async_engine
- api/security.py
- Doc Drift Auditor
- Two-Tier Gold & RAG
- test_silver_transform_v2.py
- test_r2_end_to_end_silver_to_gold_zero_local_disk
- Competition Cards & Detail
- Analytics Dashboard Page
- test_profile.py
- R2 CV PDF Storage
- Qdrant Vector Store
- bronze_validate.py
- re
- re
- V1 LLM Extraction
- test_silver_schema.py
- TypeScript Compiler Config
- TLCN Thesis Report
- test_app_config_qdrant_resolution_and_env_example
- run_gold_pipeline
- silver_eval.py
- Silver Progress Presentation
- TASK-SLV-01: Hybrid DE vs LLM Extraction Study
- Prefect Medallion Flow
- CloudflareWorkersAIEmbeddings
- In-Repo Task Registry & Deliverables Ledger
- R2 & Backup Env Vars
- middleware/security.py
- test_qa01_tech_decision_audit.py
- Deliverable: Data Contract & Quality Gate Tự động giữa Các Layer (`TASK-DQ-03`)
- Academic Research Skill
- validate_delivery_package
- Deliverable: Xây dựng Golden Dataset & Đo Độ chính xác Trích xuất Lớp Bạc theo Từng Field
- test_bronze_validation_dq01.py
- dependencies.py
- upload_to_bronze_with_result
- 4_analytics_gold.py
- Docker Compose Services
- Cloudflare Workers Embeddings
- config.py
- Competitions Explorer Page
- Deliverable: Validate Lớp Đồng (Bronze) — Tính đầy đủ, Bất biến, Truy vết Nguồn gốc & Idempotent Re-crawl
- SPEC-0003: Gold Layer Kimball Star Schema & Data Marts
- Profile Request Validation
- silver_eval.py
- Docker & Infra Tests
- rag_ingest.py
- test_silver_schema.py
- Anti-Slop Scientific Skill
- Docker Build & Profiles
- Web Container Env Config
- test_silver_eval_dq02.py
- V2 Discovery Unit Tests
- Postgres Container Env
- validate_ollama.py
- Thesis Formatting Validator
- Prefect Container Config
- Architecture Diagram Core
- GitHub Actions Steps
- PercentileSemanticChunker
- Weekly pg_dump Workflow
- httpx
- evaluate_from_r2
- Container Resource Limits
- Metabase Container Env
- Qdrant Container Config
- Medallion Layer Deliverables
- Keep-Alive & DQ Workflow
- compute_cases_sha256
- TASK-DQ-01-bronze-validation-report.md
- Full Cloud Stack Summary
- ADR-0002 Free-Tier Cloud
- Security Gates & HF-01
- Literature & SOTA Matrix
- URL Link Verifier Skill
- Container Healthchecks
- classify_error_cause
- VectorRAG & GraphRAG
- _attach_crawler_patches
- health_check
- Feasibility & T01 Review
- NT-014 Academic Competition Landscape Survey & Adaptive Ingestion
- 4_analytics_gold.py
- test_data_contracts_dq03.py
- AGENTS.md Universal AI Agent Operating Contract
- Web Sprint 02 Deliverables
- test_rag_and_openapi.py
- json
- Deliverable Template & Runbook
- Local Dev & Admin Docs
- score_bipartite_array
- Cloud & Infra Deliverables
- Workflow Input Parameters
- Weekly Backup Job Config
- seed_local_users
- Vercel Proxy & TTL Cache
- Gemini Workspace Directives
- .analyze_text
- _sync_query_rag
- Academic & Ops Layer
- Cloud Free-Tier Risk & Failover Matrix (R1-R6)
- Competitor Benchmark Skill
- _extract_det_dict_from_bronze
- Student Mini-CV Profile
- Claude Code Guardrails
- PostCSS Configuration
- Web Favicon SVG
- Team Role Matching
- ACDP Architecture Diagram
- R2 & DuckDB Core
- Deliverables Ledger Sync
- TimelineStage
- quality
- ADR-0001 Inception Stack
- ADR-0002 Cloud Defense
- TLCN vs KLTN Phases
- 3-Tier Discovery Layer
- Path
- DIR-011 Tabula Rasa
- DIR-012 Temporal Anchor
- DIR-015 Lean TLCN Scope
- DIR-017 Zero Doc Drift
- DIR-023 TLCN-KLTN Tiering
- ACDP Package Stub
- _InMemoryR2Stub
- _attach_crawler_patches
- parse_date_value
- acdp-silver-competition.odcs.yaml
- properties
- CompetitionExtractionResult
- servers
- AppConfig
- schema
- slaProperties
- description
- team

## God Nodes (most connected - your core abstractions)
1. `User` - 49 edges
2. `environment` - 48 edges
3. `AppConfig` - 46 edges
4. `Competition` - 43 edges
5. `build_gold_star_schema()` - 27 edges
6. `parse_date_value()` - 24 edges
7. `run_silver_transform()` - 23 edges
8. `build_gold_star_schema()` - 22 edges
9. `validate_silver_records_pydantic()` - 22 edges
10. `normalize_canonical_url()` - 21 edges

## Surprising Connections (you probably didn't know these)
- `3.1. Kết quả Khử trùng trên Fixture Chuẩn & Dữ liệu Live Cloudflare R2 (Phương án A — Chỉ đọc)` --references--> `audit_local_source()`  [INFERRED]
  docs/deliverables/TASK-DQ-04-entity-resolution-and-dedup.md → src/acdp/v2/data_contracts.py
- `3.2. Kết quả kiểm chứng Re-crawl 2 lần liên tiếp & Khóa bất biến R2 (`codetour.org`)` --references--> `upload_to_bronze_with_result()`  [INFERRED]
  docs/deliverables/TASK-DQ-01-bronze-validation-report.md → src/acdp/v2/bronze_crawl.py
- `2.2. Luật So khớp 5 Tầng & Cơ chế Chống Gộp Nhầm` --references--> `_SeasonConsistentUnionFind`  [INFERRED]
  docs/deliverables/TASK-DQ-04-entity-resolution-and-dedup.md → src/acdp/v2/entity_resolution.py
- `2.2. Quy ước Tính điểm cho Trường Nullable & Dữ liệu Lồng nhau` --references--> `score_bipartite_array()`  [INFERRED]
  docs/deliverables/TASK-DQ-02-silver-golden-dataset-accuracy.md → src/acdp/v2/silver_eval.py
- `_dirty_extract()` --calls--> `CompetitionExtractionResult`  [INFERRED]
  tests/test_data_contracts_dq03.py → src/acdp/v2/schemas.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **ACDP v2 Medallion Lakehouse & Serving Flow** — readme_three_tier_discovery, readme_bronze_layer, readme_silver_layer, readme_gold_layer, readme_dual_layer_rag, readme_serving_web_oltp, readme_cloud_ops [EXTRACTED 1.00]
- **ACDP Agent Governance & Prompt Execution Standards** — docs_frameworks_agent_skill_engineering_spec_doc, docs_frameworks_prompt_execution_framework_doc, docs_frameworks_team_directives_doc [EXTRACTED 1.00]
- **AI Agent Governance & Workspace Contracts** — agents_operating_contract, claude_standing_brief, gemini_workspace_rules, agents_skills_readme_registry [EXTRACTED 1.00]
- **Cycle 06 Medallion v2 Pipeline (Discovery -> Silver -> Two-Tier Gold -> Dual-Layer RAG)** — docs_deliverables_task_ing_03_three_tier_discovery_implementation_discovery_v2_module, docs_deliverables_task_slv_01_hybrid_de_vs_llm_extraction_study_deterministic_sandwich, docs_deliverables_task_slv_02_silver_schema_and_parquet_validation_visual_dossier_dossier, docs_deliverables_task_gld_02_two_tier_gold_and_dual_layer_rag_implementation_v2_gold_star_schema, docs_deliverables_task_gld_01_kimball_star_schema_audit_and_alternatives_dual_layer_rag [EXTRACTED 1.00]
- **Pre-Deployment OWASP Security, RBAC Admin & Student UX Cleanup** — docs_deliverables_task_sec_00_pre_deployment_security_and_owasp_report_gates_g1_g8, docs_deliverables_task_sec_02_rbac_admin_api_and_portal_implementation_admin_router, docs_deliverables_task_hf_01_fe_ux_cleanup_and_root_sync_deliverable [EXTRACTED 1.00]
- **Core Team Standing Directives** — agents_dir_011_tabula_rasa, agents_dir_012_temporal_grounding, agents_dir_015_lean_tlcn_stack, agents_dir_016_oltp_olap_split, agents_dir_017_atomic_decision_sync, agents_dir_018_in_repo_tasks, agents_dir_022_v2_pipeline_scope, agents_dir_023_tlcn_kltn_tiering, agents_dir_024_delivery_gate [EXTRACTED 1.00]
- **DIR-018 In-Repo Task Synchronization Artifacts** — docs_tasks_task_registry_in_repo_task_registry, docs_tasks_task_registry_tasks_data_json, docs_tasks_task_registry_index_html, agents_skills_repo_task_manager_scripts_sync_tasks [EXTRACTED 1.00]
- **GraphRAG Extraction Pipeline** — docs_assets_arch_chunking, docs_assets_arch_llm_gliner, docs_assets_arch_ontology_triples, docs_assets_arch_knowledge_graph [EXTRACTED 1.00]
- **Medallion Data Pipeline Flow** — docs_assets_arch_competition_sources, docs_assets_arch_bronze_layer, docs_assets_arch_silver_layer, docs_assets_arch_gold_layer, docs_assets_arch_serving_layer [EXTRACTED 1.00]
- **Bronze Object Storage Candidates Evaluated** — docs_deliverables_nt_018_bronze_storage_and_table_format_evaluation_local_posix, docs_deliverables_nt_018_bronze_storage_and_table_format_evaluation_seaweedfs, docs_deliverables_nt_018_bronze_storage_and_table_format_evaluation_minio, docs_deliverables_nt_018_bronze_storage_and_table_format_evaluation_cloudflare_r2 [EXTRACTED 1.00]
- **Open Table Format Candidates Evaluated** — docs_deliverables_nt_018_bronze_storage_and_table_format_evaluation_delta_lake, docs_deliverables_nt_018_bronze_storage_and_table_format_evaluation_apache_iceberg, docs_deliverables_nt_018_bronze_storage_and_table_format_evaluation_lance_format, docs_deliverables_nt_018_bronze_storage_and_table_format_evaluation_apache_hudi [EXTRACTED 1.00]
- **Silver v2 Deterministic Sandwich, Schema v2 (G1-G8), Explicit ZSTD Parquet & RAG Ingest** — docs_deliverables_task_slv_02_silver_schema_and_parquet_validation_doc, docs_deliverables_task_slv_03_hybrid_sandwich_and_rag_silver_implementation_doc, docs_deliverables_task_slv_04_silver_schema_v2_and_parquet_implementation_doc, docs_experiments_0001_rag_baseline_evaluation_doc [EXTRACTED 1.00]
- **Traditional VectorRAG Pipeline** — docs_assets_arch_chunking, docs_assets_arch_embedding, docs_assets_arch_vectordb, docs_assets_arch_llm [EXTRACTED 1.00]
- **Cycle 07 Full Cloud Free-Tier Infrastructure Tasks** — docs_tasks_task_registry_task_cld_04, docs_tasks_task_registry_task_cld_05, docs_tasks_task_registry_task_cld_06, docs_tasks_task_registry_task_cld_07 [INFERRED 0.95]
- **Cycle 06 v2 Medallion Pipeline Tasks** — docs_tasks_task_registry_task_ing_03, docs_tasks_task_registry_task_brz_02, docs_tasks_task_registry_task_slv_03, docs_tasks_task_registry_task_slv_04, docs_tasks_task_registry_task_gld_02 [INFERRED 0.95]

## Communities (171 total, 32 thin omitted)

### Community 0 - "discovery.py"
Cohesion: 0.06
Nodes (32): apply_conditional_http_checks(), build_seed_candidates(), canonicalize_url(), compute_relevance_score(), _contains_keyword(), deduplicate_and_rank(), DiscoveredCandidate, DiscoveryManifest (+24 more)

### Community 1 - "Analytics API Router"
Cohesion: 0.07
Nodes (26): get_analytics_overview(), get_analytics_seasonality(), get_competition_detail(), list_competitions(), AnalyticsDashboardDTO, DomainMetricDTO, HealthResponse, KpiOverviewDTO (+18 more)

### Community 2 - "silver_transform.py"
Cohesion: 0.06
Nodes (30): validate_bronze_to_silver_handoff(), apply_post_llm_guards(), build_bounded_llm_markdown(), build_llm_user_prompt(), _canonical_domain(), clean_markdown_text(), _contains_tech_term(), _create_instructor_client() (+22 more)

### Community 3 - "Ollama Validation Bridge"
Cohesion: 0.10
Nodes (11): run_all_tests(), test_dns_resolution(), test_single_url_verification(), test_url_cleaning(), generate_markdown_report(), is_valid_domain_string(), LinkOccurrence, LinkVerificationResult (+3 more)

### Community 4 - "JWT Auth & Seeding"
Cohesion: 0.14
Nodes (14): UserSession, get_me(), login(), logout(), refresh_tokens(), register(), _set_refresh_cookie(), _to_profile() (+6 more)

### Community 5 - "data_contracts.py"
Cohesion: 0.07
Nodes (26): _arrow_tables_to_raw_dicts(), audit_local_source(), audit_r2_silver_and_gold(), _build_arrow_tables_from_raw_dicts(), _build_gate_report(), _check_anti_noise_url_c03(), _check_official_url_c02(), _check_scope_c08() (+18 more)

### Community 6 - "gold_star_schema.py"
Cohesion: 0.05
Nodes (33): _safe_year(), build_gold_star_schema(), _register_date(), _register_organizer(), build_metabase_r2_init_sql(), build_motherduck_r2_init_sql(), classify_competition_domains(), classify_organizer_tier() (+25 more)

### Community 7 - "Admin & DuckDB Refresh"
Cohesion: 0.06
Nodes (25): _get_or_init_shared_connection(), _hydrate_gold_entities_from_r2(), refresh_duckdb_r2_connection(), reset_duckdb_connection(), get_admin_openapi(), get_admin_swagger_docs(), get_admin_telemetry(), list_admin_users() (+17 more)

### Community 8 - "Cloud Environment Config"
Cohesion: 0.05
Nodes (40): environment, ADMIN_EMAILS, BRONZE_STORAGE_BACKEND, CHAT_MODEL, CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN, CORS_ORIGIN_REGEX, CORS_ORIGINS (+32 more)

### Community 9 - "V2 Pydantic Schemas"
Cohesion: 0.17
Nodes (3): clean_placeholder(), _clean_string_list(), PrizeTier

### Community 10 - "Next.js Web Dependencies"
Cohesion: 0.07
Nodes (37): dependencies, lucide-react@^0.511.0, next@^16.4.0, react@^19.1.0, react-dom@^19.1.0, react-is@^19.1.0, recharts@^2.15.3, devDependencies (+29 more)

### Community 11 - "Student Profile Router"
Cohesion: 0.14
Nodes (13): User, UserProfile, _compute_completeness(), delete_my_cv_pdf(), download_student_cv_pdf(), get_my_profile(), _get_or_create_profile(), get_public_profile() (+5 more)

### Community 12 - "Deliverable: Entity Resolution & Khử trùng Cuộc thi Đa nguồn, Đa mùa giải (`TASK-DQ-04`)"
Cohesion: 0.10
Nodes (18): 1. Tóm tắt điều hành & Ma trận Kiểm chứng 3 Trục, 2.1. Quy chuẩn Khóa Tự nhiên (`natural_key`) & Khóa Thực thể (`competition_key`), 2.2. Luật So khớp 5 Tầng & Cơ chế Chống Gộp Nhầm, 2. Thiết kế Khóa Tự nhiên & Pipeline Entity Resolution 5 Bước, 3.1. Kết quả Khử trùng trên Fixture Chuẩn & Dữ liệu Live Cloudflare R2 (Phương án A — Chỉ đọc), 3.2. Benchmark Mở rộng Theo Quy mô (`10` $\rightarrow$ `500` bản ghi): Temporal Blocking vs Naive vs DuckDB SQL, 3. Benchmark & Kết quả Kiểm chứng Thực nghiệm, 4. Quyết định Kiến trúc & Điểm Nhấn Phản biện Hội đồng (+10 more)

### Community 13 - "main.py"
Cohesion: 0.08
Nodes (5): get_db_session(), init_oltp_schema(), lifespan(), anyio_backend(), api_client()

### Community 14 - "bronze_crawl.py"
Cohesion: 0.13
Nodes (13): crawl_urls_to_bronze(), extract_primary_http_status(), find_latest_bronze_snapshot(), _load_urls_from_r2_discovery(), main(), _merge_unique_urls(), _normalize_url_for_compare(), package_bronze_html() (+5 more)

### Community 15 - "RAG Chat Router"
Cohesion: 0.16
Nodes (13): ChatMessage, ChatSession, delete_chat_session(), _handle_rag_chat(), list_chat_sessions(), list_session_messages(), rag_chat(), rag_query_alias() (+5 more)

### Community 16 - "Bronze Storage Evaluation"
Cohesion: 0.07
Nodes (26): Planned ADR-0003 (Bronze Storage & Table Format), Apache Hudi (Rejected, JVM/Spark Dependent), Apache Iceberg (pyiceberg), ACDP Bronze Layer, Cloudflare R2 (Zero Egress Fees), Crawl4AI + Playwright Web Crawler, Data Swamp Risk, Delta Lake (delta-rs / deltalake 0.25+ & delta-kernel-rs) (+18 more)

### Community 17 - "rag_eval.py"
Cohesion: 0.07
Nodes (27): src/acdp/config.py (Groq qwen3.8-27b & OpenRouter gemma-4-31b), docs/experiments/data/0001-golden-queries.jsonl, src/acdp/api/services/rag_service.py (Gold OBT Pre-Filtering), NT-012 Dual-Layer RAG & Ragas Harness Visual Dossier, EXP-0001 3-System RAG Ablation (Naive Dense, BM25, Dual-Layer), Qdrant Cloud Vector Index (acdp_competitions_bge_m3, 778 points), EXP-0001 Ragas Target Scorecard, RetrievedChunk (+19 more)

### Community 18 - "PostgreSQL OLTP Models"
Cohesion: 0.12
Nodes (8): SavedCompetition, utc_now(), delete_bookmark(), list_bookmarks(), save_bookmark(), BookmarkCreateRequest, BookmarkDTO, check_competition_name()

### Community 19 - "Web App Layout & Fonts"
Cohesion: 0.15
Nodes (17): beVietnam, jakarta, jetbrainsMono, metadata, RootLayout(), LogoFull(), LogoMark(), LogoMonochrome() (+9 more)

### Community 20 - "RFC-0001 & BI Boundary"
Cohesion: 0.12
Nodes (11): Tier 3: Metabase Docker (--profile bi, On-Demand Local Only, 0 MB Default), Tier 2: MotherDuck Lite Free (Cloud DataOps SQL Workbench, $0/mo), TASK-CLD-02 Visual Dossier (HTML), Tier 1: Web /dashboard (Next.js 16 + Recharts on 6 mart_* Tables), TASK-CLD-03 Visual Dossier (HTML), DUCKDB_R2_TABLE_CACHE=true (15 Gold Parquets, 5.0 ms Warm, 300.2x Speedup), TASK-CLD-04 Supabase OLTP & DuckDB Direct-on-R2 Implementation, Supavisor :6543 Guard (NullPool + statement_cache_size=0 + TLS) (+3 more)

### Community 21 - "Admin UI & API Client"
Cohesion: 0.08
Nodes (30): buildCompetitionScopes(), CopilotPage(), dynamic, metadata, CompetitionScopeOption, CopilotWorkspace(), SAMPLE_PROMPTS, UiMessage (+22 more)

### Community 22 - "Web Portal Pages"
Cohesion: 0.12
Nodes (25): AdminPage(), OpenApiPreview, RateLimitBlockEvent, BookmarksPage(), LoginPage(), formatBytes(), HCMUTE_MAJORS, ProfilePage() (+17 more)

### Community 23 - "build_gold_star_schema"
Cohesion: 0.13
Nodes (8): build_gold_star_schema(), classify_competition_domains(), classify_team_profile(), _create_data_marts_and_aliases(), _create_star_schema_ddl(), export_gold_parquet_and_sync_r2(), is_participation_free(), normalize_mode()

### Community 24 - "cloud_ops.py"
Cohesion: 0.16
Nodes (8): _async_keep_alive_and_check_supabase(), check_r2_gold_data_quality(), format_markdown_summary(), keep_alive_and_check_qdrant(), keep_alive_and_check_supabase(), main(), ping_serving_api(), run_oltp_pg_dump_backup()

### Community 25 - "rag_service.py"
Cohesion: 0.07
Nodes (20): get_duckdb_conn(), get_duckdb(), answer_with_contexts(), build_gold_filter(), _build_openai_messages(), _fallback_duckdb_gold_search(), _generate_answer_with_fallback(), _generate_with_litellm_router() (+12 more)

### Community 27 - "api/security.py"
Cohesion: 0.15
Nodes (4): create_access_token(), decode_access_token(), generate_refresh_token(), verify_password()

### Community 28 - "Doc Drift Auditor"
Cohesion: 0.16
Nodes (22): AuditFinding, check_canonical_fact_drift(), check_directive_sync(), check_internal_markdown_links(), check_skill_registry_parity(), _classify_tier(), compute_blast_radius(), discover_skills() (+14 more)

### Community 29 - "Two-Tier Gold & RAG"
Cohesion: 0.14
Nodes (14): TASK-GLD-01: Kimball Star Schema Audit & Alternatives, Two-Tier Gold Architecture (Kimball Core + OBT Marts), TASK-GLD-01 Visual Dossier (HTML), TASK-GLD-02: Two-Tier Gold & Dual-Layer RAG Implementation, v2/gold_star_schema.py (Two-Tier Gold Builder), TASK-GLD-02 Visual Dossier (HTML), TASK-ING-01: Search Pattern & Free-Tier Crawling Study, 3-Tier Zero-Cost Discovery Architecture (+6 more)

### Community 30 - "test_silver_transform_v2.py"
Cohesion: 0.17
Nodes (4): test_deterministic_extraction_jsonld_og_official_links_and_regex(), test_dir022_scope_gate_and_media_partner_dedup(), test_post_llm_guards_enforce_canonical_url(), test_split_bronze_pages_and_in_ram_clean_markdown()

### Community 32 - "Competition Cards & Detail"
Cohesion: 0.16
Nodes (18): CompetitionDetailPage(), dynamic, extractHost(), metadata, dynamic, HomePage(), QUICK_FILTERS, BookmarkButton() (+10 more)

### Community 33 - "Analytics Dashboard Page"
Cohesion: 0.20
Nodes (15): CompetitionCardProps, DashboardPage(), dynamic, metadata, ChartCard(), ChartCardProps, DomainBarChart(), MODE_COLORS (+7 more)

### Community 34 - "test_profile.py"
Cohesion: 0.21
Nodes (5): FakeCvStorageService, _register_and_login(), test_profile_pdf_upload_download_delete_and_privacy(), test_profile_requires_auth_and_defaults_for_new_student(), test_profile_upsert_syncs_user_normalizes_skills_and_validates_urls()

### Community 35 - "R2 CV PDF Storage"
Cohesion: 0.11
Nodes (4): upload_my_cv_pdf(), CvStorageService, get_cv_storage_service(), sanitize_pdf_filename()

### Community 36 - "Qdrant Vector Store"
Cohesion: 0.12
Nodes (8): build_chunker(), chunk_single_document(), clean_markdown(), ensure_collection(), get_vector_store(), ingest(), list_latest_bronze_snapshots(), load_competition_documents()

### Community 37 - "bronze_validate.py"
Cohesion: 0.14
Nodes (17): audit_bronze_bucket(), _audit_downstream_traceability(), backfill_v2_bronze_metadata(), BronzeObjectAudit, BronzeValidationReport, _classify_bronze_key(), _count_domain_html_objects(), DownstreamTraceabilityAudit (+9 more)

### Community 38 - "re"
Cohesion: 0.05
Nodes (39): audit_near_duplicates_duckdb(), _build_profile(), canonicalize_official_url(), classify_url_authority(), _count_non_null_scalars(), EntityClusterSummary, EntityMatchDecision, _EntityProfile (+31 more)

### Community 39 - "re"
Cohesion: 0.09
Nodes (13): main(), validate_benchmark(), main(), validate_slides(), compute_scorecard(), main(), main(), validate_component() (+5 more)

### Community 40 - "V1 LLM Extraction"
Cohesion: 0.13
Nodes (6): call_chat_completion(), create_llm_client(), clean_markdown_content(), extract_competition_from_markdown(), parse_bronze_key(), process_bronze_bucket()

### Community 41 - "test_silver_schema.py"
Cohesion: 0.12
Nodes (7): test_competition_extraction_result_coercion(), test_competition_extraction_result_container(), test_empty_document_handling(), test_prize_tier_validation(), test_silver_schema_v2_gap_g1_g8_resolved(), test_silver_v2_explicit_pyarrow_zstd_and_timeline_stages(), test_timeline_stage_validation()

### Community 42 - "TypeScript Compiler Config"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 43 - "TLCN Thesis Report"
Cohesion: 0.13
Nodes (19): BronzeRecord Schema, Four Student Competition Bottlenecks, Gold Dimensional Data Marts, Modular Hybrid RAG & Ragas Evaluation, 4-Layer Lean Medallion Lakehouse Architecture, Báo cáo Tiểu luận Chuyên ngành KTDL, 7 Sample Competitions Bronze Benchmark, SilverCompetitionRecord Schema (+11 more)

### Community 45 - "run_gold_pipeline"
Cohesion: 0.33
Nodes (3): run_gold_pipeline(), verify_analytics(), verify_analytics_from_r2()

### Community 46 - "silver_eval.py"
Cohesion: 0.23
Nodes (7): _compute_prf(), ErrorInstance, evaluate_deterministic_vs_hybrid(), evaluate_predictions(), FieldMetricSummary, GoldenDataset, _is_missing_field_value()

### Community 47 - "Silver Progress Presentation"
Cohesion: 0.11
Nodes (14): Bronze Delta Lake (delta-rs + Zstd L3), Báo Cáo Tiến Độ Lớp Bạc (Silver Layer) Presentation, generate_fingerprint() Deduplication, Lean Medallion Lakehouse Architecture, SilverCompetitionRecord (11 Core Fields, Pydantic v2), Zstandard L3 Compression Benchmark (80.2% Savings), src/acdp/1_crawl_to_bronze.py (upload_to_bronze), src/acdp/2_instruction.py (push_silver_records_to_r2) (+6 more)

### Community 48 - "TASK-SLV-01: Hybrid DE vs LLM Extraction Study"
Cohesion: 0.20
Nodes (10): Vietnam Dedicated Competition Landing Pages Expansion Report (15 Verified URLs), Dual-Layer RAG (Silver Text + Gold Metadata), TASK-SLV-01: Hybrid DE vs LLM Extraction Study, Deterministic Sandwich ETL Pattern, TASK-SLV-01 Visual Dossier (HTML), TASK-SLV-02: Silver Schema & Parquet Validation Audit, Normalized Silver Parquet Tables (competitions, prizes, timeline_stages) with Explicit PyArrow Schema, TASK-SLV-04: Silver Schema v2 (G1-G8) & PyArrow Explicit ZSTD Parquet (+2 more)

### Community 49 - "Prefect Medallion Flow"
Cohesion: 0.18
Nodes (6): _list_r2_keys(), medallion_lakehouse_flow(), task_build_gold_r2(), task_extract_silver(), task_ingest_bronze(), task_ingest_qdrant()

### Community 50 - "CloudflareWorkersAIEmbeddings"
Cohesion: 0.19
Nodes (3): CloudflareWorkersAIEmbeddings, EmbeddingRateLimitError, _is_rate_limit_error()

### Community 51 - "In-Repo Task Registry & Deliverables Ledger"
Cohesion: 0.50
Nodes (4): DIR-018 (In-Repo Task Management), In-Repo Task Registry & Deliverables Ledger, Interactive Task Portal (index.html), tasks-data.json

### Community 52 - "R2 & Backup Env Vars"
Cohesion: 0.17
Nodes (17): AWS_ACCESS_KEY_ID, AWS_ENDPOINT_URL, AWS_REGION, AWS_SECRET_ACCESS_KEY, BUCKET_NAME, OLTP_BACKUP_R2_PREFIX, OLTP_BACKUP_RETENTION_DAYS, POSTGRES_MODE (+9 more)

### Community 53 - "middleware/security.py"
Cohesion: 0.05
Nodes (18): apply_security_headers(), enforce_ai_rate_limit(), extract_client_ip(), get_rate_limit_stats(), _masked_internal_error_response(), MultiTierRateLimiter, RateLimitDecision, register_security_exception_handlers() (+10 more)

### Community 54 - "test_qa01_tech_decision_audit.py"
Cohesion: 0.12
Nodes (6): test_config_r2_exclusive_and_llm_guardrails(), test_deliverable_covers_all_eight_decisions_and_seven_core_components(), test_dir024_and_standard_delivery_gate_synced(), test_docker_compose_zero_latest_and_ram_budget(), test_keep_alive_workflow_daily_and_weekly_backup(), test_rfcs_exist_with_valid_lifecycle_status()

### Community 55 - "Deliverable: Data Contract & Quality Gate Tự động giữa Các Layer (`TASK-DQ-03`)"
Cohesion: 0.12
Nodes (17): 1. Tóm tắt điều hành & Ma trận Kiểm chứng 3 Trục, 2.1. Phân tách 19 Quy tắc Chốt chặn (`14 CRITICAL` vs `5 WARNING`), 2. Kiến trúc Hợp đồng Dữ liệu (ODCS v3.2) & Cơ chế WAP Circuit Breaker, 3.1. Đối chứng Fixture Hợp lệ vs Fixture Vi phạm & Kiểm định Live R2 (Phương án A — Chỉ đọc), 3.2. Chi tiết 5 Bản ghi Vi phạm Lịch sử Phát hiện trên Live Cloudflare R2 (`s3://acdp-lakehouse/silver/`), 3.3. Benchmark Tốc độ Thực thi Tier A (Pydantic v2) vs Tier B (DuckDB SQL), 3. Benchmark & Kết quả Kiểm chứng Thực nghiệm, 4. Luận cứ Phản biện Hội đồng & Quyết định Kiến trúc (+9 more)

### Community 56 - "Academic Research Skill"
Cohesion: 0.14
Nodes (11): Academic Researcher Skill, 4-Step Scientific Execution Protocol, Information Extraction, Lakehouse Architectures, docs/academic/literature-review.md, Retrieval-Augmented Generation (RAG), docs/academic/references.bib, examples/sample_sota_matrix.md (+3 more)

### Community 57 - "validate_delivery_package"
Cohesion: 0.16
Nodes (3): _extract_section(), validate_delivery_package(), TestStandardDeliveryGate

### Community 58 - "Deliverable: Xây dựng Golden Dataset & Đo Độ chính xác Trích xuất Lớp Bạc theo Từng Field"
Cohesion: 0.13
Nodes (14): 1. Tóm tắt điều hành & Ma trận Kiểm chứng 3 Trục, 3.1. Bảng Điểm Chi tiết theo Từng Field (21 Trường × 10 Cuộc thi), 3.2. Đối chiếu Deterministic Parser vs Hybrid Silver Pipeline (7 Trường giao nhau), 3.3. Kết quả Cải thiện Before vs After (Phương án A — Vá lỗi Tất định, Không ghi đè R2), 3.4. Bảng Phân loại Nguyên nhân Lỗi (Error Taxonomy `E1–E5`), 3. Benchmark & Kết quả Đo đạc Thực nghiệm, 4. Luận cứ Phản biện Hội đồng, 5. Hướng dẫn Kiểm thử Thủ công, Triển khai CLI & Kịch bản Demo GVHD (+6 more)

### Community 59 - "test_bronze_validation_dq01.py"
Cohesion: 0.14
Nodes (14): _FakeBody, FakeR2Client, _parquet_bytes(), test_bronze_audit_detects_invalid_utf8_and_missing_boundary(), test_bronze_audit_detects_missing_metadata_and_hash_tampering(), test_bronze_audit_detects_uncontrolled_duplicate_and_dangling_silver(), test_bronze_audit_passes_for_compliant_v2_and_downstream_silver_gold(), test_bronze_backfill_preserves_exact_bytes_and_populates_provenance() (+6 more)

### Community 60 - "dependencies.py"
Cohesion: 0.18
Nodes (5): get_current_user(), get_optional_user(), require_admin(), require_lecturer_or_admin(), _sync_admin_role_if_listed()

### Community 61 - "upload_to_bronze_with_result"
Cohesion: 0.18
Nodes (5): BronzeUploadResult, compute_content_sha256(), sanitize_s3_meta_value(), upload_to_bronze(), upload_to_bronze_with_result()

### Community 62 - "4_analytics_gold.py"
Cohesion: 0.15
Nodes (7): _competition_richness_score(), _deduplicate_competition_payloads(), _extract_batch_sort_key(), load_silver_competitions(), load_silver_competitions_from_r2(), load_silver_competitions_with_source(), parse_silver_key()

### Community 63 - "Docker Compose Services"
Cohesion: 0.13
Nodes (14): container_name, image, ports, profiles, restart, user, volumes, services (+6 more)

### Community 64 - "Cloudflare Workers Embeddings"
Cohesion: 0.17
Nodes (3): CloudflareWorkersAIEmbeddings, EmbeddingRateLimitError, _is_rate_limit_error()

### Community 65 - "config.py"
Cohesion: 0.06
Nodes (11): test_bronze_r2_key_generation_logic(), test_empty_content_check_logic(), test_markdown_utf8_storage_and_sha256_integrity(), test_upload_to_bronze_r2_and_empty_skip(), test_v2_package_bronze_html_with_boundaries(), test_v2_upload_to_bronze_raw_html_r2_and_empty_skip(), test_currency_normalization_edge_cases(), test_date_resolution_and_academic_terms() (+3 more)

### Community 66 - "Competitions Explorer Page"
Cohesion: 0.18
Nodes (12): CompetitionsPage(), dynamic, FILTER_LABELS, metadata, VALUE_LABELS, DOMAIN_OPTIONS, FilterForm(), FilterSidebar() (+4 more)

### Community 67 - "Deliverable: Validate Lớp Đồng (Bronze) — Tính đầy đủ, Bất biến, Truy vết Nguồn gốc & Idempotent Re-crawl"
Cohesion: 0.12
Nodes (16): 1. Tóm tắt điều hành & Ma trận Kiểm chứng 3 Trục, 2.1. Đặc tả 10 trường Metadata Nguồn gốc trên Cloudflare R2, 2.2. Xử lý tương thích với dữ liệu lịch sử (Phương án A), 2. Thiết kế Siêu dữ liệu Nguồn gốc, Bất biến & Idempotent Re-crawl, 3.1. Bảng đo đạc Trước và Sau Backfill (`s3://acdp-lakehouse/bronze/`), 3.2. Kết quả kiểm chứng Re-crawl 2 lần liên tiếp & Khóa bất biến R2 (`codetour.org`), 3. Benchmark & Kết quả Kiểm chứng Thực nghiệm trên Cloudflare R2, 4. Luận cứ Phản biện Hội đồng & So sánh Open Table Format (Iceberg / Delta Lake) (+8 more)

### Community 68 - "SPEC-0003: Gold Layer Kimball Star Schema & Data Marts"
Cohesion: 0.13
Nodes (26): DIR-022 Student Tech Scope, Official Site Resolution & v2 Pipeline, TASK-HF-01: Frontend UX Cleanup & Root Docs Sync, TASK-HF-01 Visual Dossier (HTML), TASK-QA-01: 3-Axis Technical Decision Audit, TASK-QA-01 Visual Dossier (HTML), ACDP R&D Tasks Hub & 4-Stage Research Lifecycle, T01: Business Analysis, Technical Feasibility & Lean Stack Alignment, T02: Competition Survey & 4-Pillar Generalized Adaptive Ingestion Architecture (+18 more)

### Community 69 - "Profile Request Validation"
Cohesion: 0.29
Nodes (4): _clean_optional_str(), _normalize_tag_list(), ProfileUpdateRequest, _validate_https_url()

### Community 70 - "silver_eval.py"
Cohesion: 0.24
Nodes (11): compare_scalar_field(), FieldSpec, _items_similar(), _norm_fee_bucket(), _normalize_date_str(), _normalize_tokens(), _normalize_url_key(), _prize_similarity() (+3 more)

### Community 71 - "Docker & Infra Tests"
Cohesion: 0.17
Nodes (4): _parse_mem_mb(), test_docker_compose_version_pinning_and_profiles(), test_dockerignore_and_dockerfile_api_hardening(), test_keep_alive_workflow_pg_dump_url_and_backup()

### Community 72 - "rag_ingest.py"
Cohesion: 0.14
Nodes (9): enrich_document_with_gold_metadata(), ensure_collection(), ingest(), list_latest_silver_markdown_snapshots(), load_competition_documents_from_silver(), load_gold_explorer_metadata(), load_silver_extraction_index(), main() (+1 more)

### Community 73 - "test_silver_schema.py"
Cohesion: 0.10
Nodes (9): clean_placeholder(), Competition, CompetitionExtractionResult, PrizeTier, TimelineStage, test_clean_placeholder(), test_competition_creation_and_normalization(), test_json_roundtrip_integrity() (+1 more)

### Community 74 - "Anti-Slop Scientific Skill"
Cohesion: 0.18
Nodes (13): detect_ai_slop.py Deterministic Linter, anti-slop-scientific-writer Skill, Hybrid Retrieval Architecture Specification Example, DuckDB vs SQLite Parquet Comparison Example, Catalog of 25 AI Structural Tropes & Anti-Patterns, Scientific Writing & Technical Documentation Style Guide, Banned AI Vocabulary & Scientific Alternatives Lexicon, doc-decision-sync Skill (+5 more)

### Community 75 - "Docker Build & Profiles"
Cohesion: 0.17
Nodes (13): build, container_name, depends_on, extra_hosts, ports, profiles, restart, context (+5 more)

### Community 76 - "Web Container Env Config"
Cohesion: 0.15
Nodes (13): condition, api, INTERNAL_API_URL, NEXT_PUBLIC_API_URL, NODE_OPTIONS, web, container_name, depends_on (+5 more)

### Community 77 - "test_silver_eval_dq02.py"
Cohesion: 0.15
Nodes (6): _make_minimal_dataset(), test_bipartite_array_f1_is_order_insensitive(), test_error_taxonomy_classifier_e1_to_e5(), test_golden_dataset_v1_schema_and_sha256_integrity(), test_nullable_ie_metrics_tp_fp_fn_tn_and_exact_match(), test_option_a_date_parser_and_sidebar_noise_regression()

### Community 78 - "V2 Discovery Unit Tests"
Cohesion: 0.18
Nodes (7): test_deduplication_and_http_304_check(), head_handler(), _run_head(), test_tier2_budget_cap_and_serper_fallback(), handler(), _run(), test_upload_manifest_to_r2()

### Community 79 - "Postgres Container Env"
Cohesion: 0.17
Nodes (12): POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, command, container_name, environment, image, ports (+4 more)

### Community 80 - "validate_ollama.py"
Cohesion: 0.27
Nodes (5): Ollama Hardware & Model Matrix, check_cli(), check_endpoint(), main(), Ollama Bridge Skill

### Community 81 - "Thesis Formatting Validator"
Cohesion: 0.33
Nodes (6): ACDP 4-Tier System Architecture Sample, FIT-HCMUTE Thesis & TLCN Guideline, Thesis Writer Skill, Bug Report Issue Template, Feature Request Issue Template, Pull Request Template

### Community 82 - "Prefect Container Config"
Cohesion: 0.18
Nodes (11): PREFECT_SERVER_API_HOST, PREFECT_UI_API_URL, command, container_name, environment, image, ports, profiles (+3 more)

### Community 83 - "Architecture Diagram Core"
Cohesion: 0.22
Nodes (11): Bronze Layer (n post, plain text), Chatbot (VectorRAG, GraphRAG), Competition Sources (Eureka, ICPC, Hackathon, CTF, Mastering IT, AI Challenge), Dashboard, Gold Layer (metrics), Graph RAG, Serving Layer, Silver Layer (list, metadata, vector matrix) (+3 more)

### Community 84 - "GitHub Actions Steps"
Cohesion: 0.24
Nodes (11): steps, name, run, uses, with, steps, enable-cache, if-no-files-found (+3 more)

### Community 85 - "PercentileSemanticChunker"
Cohesion: 0.31
Nodes (3): build_chunker(), chunk_single_document(), PercentileSemanticChunker

### Community 86 - "Weekly pg_dump Workflow"
Cohesion: 0.20
Nodes (10): run_pg_dump, on, schedule, workflow_dispatch, default, description, required, type (+2 more)

### Community 88 - "evaluate_from_r2"
Cohesion: 0.21
Nodes (7): evaluate_from_r2(), load_golden_dataset(), main(), _parse_args(), print_report_summary(), _save_report_to_r2(), SilverEvaluationReport

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

### Community 94 - "compute_cases_sha256"
Cohesion: 0.29
Nodes (3): GoldenGroundTruth, GoldenPrize, GoldenStage

### Community 95 - "TASK-DQ-01-bronze-validation-report.md"
Cohesion: 0.11
Nodes (17): TASK-SLV-03: Hybrid Deterministic Sandwich & Silver RAG Implementation, 4-Step Hybrid Deterministic Sandwich (Extract, Scope Gate DIR-022, Bounded Instructor LLM, Validate & Load), Silver-to-Qdrant RAG Ingest (26 Clean Markdown -> 648 bge-m3 Chunks), TASK-SLV-03 Visual Dossier (HTML), EXP-0001: Dual-Layer RAG (v2) Baseline Evaluation Protocol (Ragas), Dual-Layer RAG (Silver Markdown bge-m3 + Gold OBT Metadata Pre-Filtering + gemini-3.5-flash-lite), ACDP Empirical Experiments & Benchmarking Hub, T13: Bronze Layer Tech Stack Evaluation (Object Storage & Open Table Format) (+9 more)

### Community 96 - "Full Cloud Stack Summary"
Cohesion: 0.25
Nodes (8): DIR-016 Web & OLTP/OLAP Split Stack, Bronze Layer (Raw Rendered HTML on Cloudflare R2), Cloud Ops & Weekly pg_dump Backups (GitHub Actions), Dual-Layer RAG & Ragas Evaluation (Qdrant + bge-m3 + Gemini 3.5 Flash Lite), Gold Layer (Two-Tier Kimball Star Schema & DuckDB httpfs), Serving & Web Portal (FastAPI + PostgreSQL 18 + Next.js 16), Silver Layer (Hybrid Deterministic Sandwich & Pydantic/Arrow Schema), 3-Tier Discovery (Sitemap/RSS/GDELT + Search APIs + ETag)

### Community 97 - "ADR-0002 Free-Tier Cloud"
Cohesion: 0.25
Nodes (3): 100% Cloud Free-Tier Stack Matrix, Keep-Alive Automation, Backup & Demo Day Protocol, 3-Tier BI Architecture & MotherDuck Lite

### Community 98 - "Security Gates & HF-01"
Cohesion: 0.40
Nodes (5): TASK-SEC-00: Pre-Deployment Security & OWASP Blueprint, TASK-SEC-00 Visual Dossier (HTML), src/acdp/api/routers/admin.py & SecurityHardeningMiddleware, TASK-SEC-02: RBAC, Admin API & /admin Portal, TASK-SEC-02 Visual Dossier (HTML)

### Community 99 - "Literature & SOTA Matrix"
Cohesion: 0.29
Nodes (7): Armbrust et al. (2021) Medallion Lakehouse, Gao et al. (2023) Modular RAG Survey, Lappas et al. (2009) Expert Team Formation, Lewis et al. (2020) DPR RAG, Sample Literature Review & SOTA Matrix, Xu et al. (2024) LLM Web Extraction, SOTA Academic Venues & Search Protocols

### Community 100 - "URL Link Verifier Skill"
Cohesion: 0.67
Nodes (3): Academic & University Domain Whitelist, HTTP Status & Anti-Bot Technical Guide, URL Link Verifier Skill

### Community 101 - "Container Healthchecks"
Cohesion: 0.57
Nodes (7): healthcheck, interval, retries, test, timeout, healthcheck, healthcheck

### Community 102 - "classify_error_cause"
Cohesion: 0.29
Nodes (3): classify_error_cause(), compute_cases_sha256(), GoldenCase

### Community 103 - "VectorRAG & GraphRAG"
Cohesion: 0.29
Nodes (7): Chunking, Embedding, Knowledge Graph, LLM, LLM / GLiNER, Ontology / Triples, VectorDB

### Community 104 - "_attach_crawler_patches"
Cohesion: 0.29
Nodes (3): _attach_crawler_patches(), _resilient_map_query_semantic_space(), _extract_query_list()

### Community 106 - "Feasibility & T01 Review"
Cohesion: 0.29
Nodes (5): NT-013 Business & Technical Feasibility Review (T01 Review), Hybrid Ingestion & Silver Entity Resolution, Seed Knowledge First & Aspect-Based Sentiment Analysis (ABSA), docs/rd-tasks/T01.md, Unstructured-to-Structured ELT (5 OLAP Dimensions)

### Community 107 - "NT-014 Academic Competition Landscape Survey & Adaptive Ingestion"
Cohesion: 0.16
Nodes (13): Bảng đăng ký Đề tài Tiểu luận Chuyên ngành, Master Specification & Initialization Prompt, 8-Dimension Survey Matrix of 18 Student Competitions, 4 Student Bottlenecks & ACDP Technical Countermeasures, Academic Grounding (Cho & Garcia-Molina, Chakrabarti, West & Dragut), NT-014 Academic Competition Landscape Survey & Adaptive Ingestion, 4-Pillar Adaptive Ingestion Architecture, 4-Stage Geographic Expansion Roadmap (+5 more)

### Community 108 - "4_analytics_gold.py"
Cohesion: 0.13
Nodes (10): _register_organizer(), build_metabase_r2_init_sql(), classify_organizer_tier(), compute_competition_key(), _compute_competition_total_prize_vnd(), export_silver_parquet(), normalize_canonical_url(), _parse_number_token() (+2 more)

### Community 109 - "test_data_contracts_dq03.py"
Cohesion: 0.12
Nodes (6): test_benchmark_runner_outputs_valid_timings(), test_bronze_to_silver_handoff_gate_c12_pass_and_fail(), test_gold_pre_publish_gate_c13_c14_catches_row_mismatch_and_bridge_drift(), test_invalid_silver_fixture_trips_all_expected_critical_rules_c01_to_c11(), test_odcs_v32_contract_yaml_valid_and_synced(), test_valid_silver_fixture_passes_all_critical_rules_with_zero_false_positives()

### Community 110 - "AGENTS.md Universal AI Agent Operating Contract"
Cohesion: 0.10
Nodes (27): AGENTS.md Universal AI Agent Operating Contract, defense-pitch-builder Skill, ACDP HTML5 Defense Slide Template, ACDP Design Tokens, Frontend Designer Skill, Progressive Disclosure Skill Loading, ACDP Agent Skills Suite & Engineering Standards, 3-Tier Skill Architecture (Discovery, Activation, Execution) (+19 more)

### Community 111 - "Web Sprint 02 Deliverables"
Cohesion: 0.33
Nodes (6): Serving & Web Layer, NT-025: FastAPI Serving Gateway & PostgreSQL 18 OLTP, NT-029: Web Sprint 02 Full-Stack Implementation, TASK-HF-01: Frontend UX Cleanup & Root Docs Sync, TASK-SEC-02: RBAC (Admin/Lecturer/Student), Admin API & /admin Portal, TASK-SRV-01: Student Mini-CV Profile Page (/profile)

### Community 112 - "test_rag_and_openapi.py"
Cohesion: 0.07
Nodes (10): CloudflareBgeM3Embedder, _embed_with_fastembed_fallback(), _get_embeddings(), _is_recoverable_rate_or_server_error(), RagUnavailableError, test_cloudflare_bge_m3_rag_pipeline_and_config(), test_openapi_31_contract_is_valid(), test_rag_chat_persistence_ungrounded_and_outage() (+2 more)

### Community 113 - "json"
Cohesion: 0.06
Nodes (19): embed_json_in_html(), load_tasks_data(), main(), render_task_registry_md(), validate_tasks_data(), TestSyncTasks, upload_to_silver(), export_openapi_schema() (+11 more)

### Community 114 - "Deliverable Template & Runbook"
Cohesion: 0.40
Nodes (3): Manual Test, CLI Deployment & Advisor Demo Runbook, 7-Section Deliverable Template Structure, docs/tasks/task-registry.md

### Community 115 - "Local Dev & Admin Docs"
Cohesion: 0.40
Nodes (4): Protected Admin Swagger UI (/api/v1/admin/docs), Local (.env.dev) vs Production Environment Separation, React Error #31 Fix (apps/web/lib/api-client.ts), scripts/seed_local_users.py (@acdp.dev Accounts)

### Community 116 - "score_bipartite_array"
Cohesion: 0.40
Nodes (4): 2.1. Phân tầng 10 Cuộc thi Golden (Scope TLCN 5–10 cuộc thi), 2.2. Quy ước Tính điểm cho Trường Nullable & Dữ liệu Lồng nhau, 2. Thiết kế Golden Dataset, Quy ước Tính điểm & Kiến trúc Đánh giá, score_bipartite_array()

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

### Community 125 - ".analyze_text"
Cohesion: 0.18
Nodes (6): AuditReport, main(), print_text_report(), SlopDetector, SlopViolation, TestSlopDetector

### Community 126 - "_sync_query_rag"
Cohesion: 0.24
Nodes (4): query_rag(), RagResponseTTLCache, RagResult, _sync_query_rag()

### Community 127 - "Academic & Ops Layer"
Cohesion: 0.50
Nodes (4): Academic & Ops Layer, RFC-0001: Spec v2 and Cloud Parity Realignment, RFC-0002: KLTN Scale Evolution Triggers, TASK-QA-01: Tech Decision Theory x Practice x Scope Audit

### Community 129 - "Cloud Free-Tier Risk & Failover Matrix (R1-R6)"
Cohesion: 0.15
Nodes (13): PercentileSemanticChunker (Pure Python, 0 DeprecationWarnings), Qdrant v1.20.2 & PG 17+/18.7 Compatibility, RFC-0001 Implementation Report (TASK-QA-01), Offline Unit Tests (61/61 Passed) & Zero Doc Drift (116 Files), Core Profile RAM Budget (1,408 MB, -26.7% vs 1,920 MB), Qdrant Failover Rebuild from R2 (RTO < 60s via acdp.v2.rag_ingest), TASK-CLD-01 Visual Dossier (HTML), Cloud Free-Tier Risk & Failover Matrix (R1-R6) (+5 more)

### Community 130 - "Competitor Benchmark Skill"
Cohesion: 0.50
Nodes (5): competitor-benchmark Skill, UVP Differentiation Matrix, Competitor Profiles & Landscape Teardowns, Competitor Benchmarks & Strategic Positioning, ACDP Market & Competitor Research Index

### Community 131 - "_extract_det_dict_from_bronze"
Cohesion: 0.33
Nodes (3): _extract_det_dict_from_bronze(), html_to_clean_markdown(), is_html_payload()

### Community 132 - "Student Mini-CV Profile"
Cohesion: 0.67
Nodes (3): TASK-SRV-01: Student Mini-CV Profile (/profile) & R2 PDF CV Storage, PostgreSQL OLTP user_profiles Table & Dual CV Support (https:// URL + R2 PDF <= 2MB), TASK-SRV-01 Visual Dossier (HTML)

### Community 141 - "TimelineStage"
Cohesion: 0.17
Nodes (5): TimelineStage, _make_valid_comp(), test_load_silver_prefers_newest_batch_and_deduplicates(), test_star_schema_bridge_allocation_and_edge_cases(), test_silver_v2_schema_validation_and_g7_rejection()

### Community 142 - "quality"
Cohesion: 0.18
Nodes (11): quality, description, engine, id, layer, mustBe, mustBeGreaterThanOrEqualTo, name (+3 more)

### Community 148 - "Path"
Cohesion: 0.18
Nodes (5): test_cli_exit_codes_and_json_report_export(), test_silver_parquet_dir_audit_pass_and_fail_via_duckdb(), test_wap_circuit_breaker_blocks_gold_star_schema_publish_on_violation(), test_wap_circuit_breaker_blocks_silver_parquet_publish_on_violation(), test_warning_rules_w01_to_w05_never_trip_circuit_breaker()

### Community 161 - "_InMemoryR2Stub"
Cohesion: 0.20
Nodes (3): _InMemoryR2Stub, test_silver_transform_strict_gate_blocks_dirty_record(), _dirty_extract()

### Community 162 - "_attach_crawler_patches"
Cohesion: 0.18
Nodes (5): _attach_crawler_patches(), _resilient_map_query_semantic_space(), _extract_query_list(), main(), upload_to_bronze()

### Community 163 - "parse_date_value"
Cohesion: 0.24
Nodes (5): _register_date(), map_academic_term(), parse_date_value(), resolve_date_sk(), resolve_effective_registration_status()

### Community 169 - "acdp-silver-competition.odcs.yaml"
Cohesion: 0.22
Nodes (8): apiVersion, dataProduct, domain, id, kind, name, status, version

### Community 171 - "properties"
Cohesion: 0.25
Nodes (8): description, enum, logicalType, name, physicalType, primaryKey, required, properties

### Community 173 - "CompetitionExtractionResult"
Cohesion: 0.15
Nodes (4): CompetitionExtractionResult, InMemoryR2Client, test_end_to_end_silver_transform_and_rag_ingest_from_silver(), _fake_extract()

### Community 174 - "servers"
Cohesion: 0.33
Nodes (6): servers, description, format, location, server, type

### Community 175 - "AppConfig"
Cohesion: 0.09
Nodes (5): AppConfig, test_g2_fail_fast_jwt_secret_validation_in_production(), test_local_backend_rejected_under_r2_exclusive_policy(), test_storage_options_cloudflare_r2_backend(), test_storage_options_custom_s3_backend_http()

### Community 177 - "schema"
Cohesion: 0.40
Nodes (5): schema, description, name, physicalName, physicalType

### Community 178 - "slaProperties"
Cohesion: 0.40
Nodes (5): slaProperties, description, property, unit, value

### Community 180 - "description"
Cohesion: 0.50
Nodes (4): description, limitations, purpose, usage

### Community 181 - "team"
Cohesion: 0.50
Nodes (4): team, name, role, username

## Knowledge Gaps
- **208 isolated node(s):** `acdp`, `Knowledge Graph`, `LLM`, `src/acdp/config.py (Groq qwen3.8-27b & OpenRouter gemma-4-31b)`, `src/acdp/api/services/rag_service.py (Gold OBT Pre-Filtering)` (+203 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1276 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **32 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SPEC-0002: Lean Data Ingestion & Bronze-to-Silver Extraction` connect `SPEC-0003: Gold Layer Kimball Star Schema & Data Marts` to `json`, `Two-Tier Gold & RAG`, `test_data_contracts_dq03.py`, `TASK-DQ-01-bronze-validation-report.md`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Are the 36 inferred relationships involving `User` (e.g. with `get_current_user()` and `get_optional_user()`) actually correct?**
  _`User` has 36 INFERRED edges - model-reasoned connections that need verification._
- **What connects `acdp`, `Knowledge Graph`, `LLM` to the rest of the system?**
  _208 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `discovery.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06241519674355495 - nodes in this community are weakly interconnected._
- **Why does `TASK-HF-01: Frontend UX Cleanup & Root Docs Sync` connect `SPEC-0003: Gold Layer Kimball Star Schema & Data Marts` to `json`, `Security Gates & HF-01`, `Competitor Benchmark Skill`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Should `Analytics API Router` be split into smaller, more focused modules?**
  _Cohesion score 0.06875 - nodes in this community are weakly interconnected._
- **Why does `ACDP R&D Tasks Hub & 4-Stage Research Lifecycle` connect `SPEC-0003: Gold Layer Kimball Star Schema & Data Marts` to `NT-014 Academic Competition Landscape Survey & Adaptive Ingestion`, `TLCN Thesis Report`, `AGENTS.md Universal AI Agent Operating Contract`, `TASK-DQ-01-bronze-validation-report.md`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._