"""Volume 25 — Git Workflow & Release Management registry (SSOT)."""

GIT_WORKFLOW_VERSION = "Volume 25 v1.0"
GIT_WORKFLOW_STATUS = "Final"
GIT_WORKFLOW_OWNER = "Ceragem CIOS Engineering"

DEPENDENCIES: tuple[str, ...] = (
    "Volume 13 Deployment & DevOps",
    "Volume 24 Development Convention",
)

BRANCH_STRATEGY: tuple[dict, ...] = (
    {
        "name": "main",
        "purpose": "Production-ready source code",
        "rules": (
            "Protected branch",
            "No direct commits",
            "Merge only from release or hotfix branches",
        ),
    },
    {
        "name": "develop",
        "purpose": "Primary integration branch",
        "rules": (
            "Active development occurs here",
            "Feature branches merge into develop",
            "Always buildable",
        ),
    },
    {
        "name": "feature/*",
        "purpose": "Individual development work",
        "examples": (
            "feature/upload-engine",
            "feature/dashboard",
            "feature/recommendation-engine",
            "feature/provider-export",
            "feature/forecast",
        ),
        "rules": ("Created from develop", "Merged back into develop", "Deleted after merge"),
    },
    {
        "name": "release/*",
        "purpose": "Release preparation",
        "examples": ("release/v1.0.0", "release/v1.1.0"),
        "activities": (
            "Final QA",
            "Documentation review",
            "Performance testing",
            "Bug fixes",
        ),
        "rules": ("No new features",),
    },
    {
        "name": "hotfix/*",
        "purpose": "Emergency production fixes",
        "examples": (
            "hotfix/login-error",
            "hotfix/upload-validation",
            "hotfix/dashboard-api",
        ),
        "rules": ("Created from main", "Merged into main", "Merged back into develop"),
    },
)

PROTECTED_BRANCHES: tuple[str, ...] = ("main", "develop")

BRANCH_PROTECTION_RULES: tuple[str, ...] = (
    "Pull Request required",
    "Code Review required",
    "CI must pass",
    "No force push",
    "No direct commits",
)

COMMIT_FORMAT = "type(scope): description"

COMMIT_TYPES: tuple[str, ...] = (
    "feat",
    "fix",
    "refactor",
    "docs",
    "style",
    "test",
    "build",
    "chore",
    "perf",
)

COMMIT_EXAMPLES: tuple[str, ...] = (
    "feat(upload): implement auto mapping engine",
    "fix(api): correct campaign export",
    "docs(metadata): update alias dictionary",
    "refactor(engine): simplify recommendation logic",
    "test(upload): add upload validation tests",
    "perf(query): optimize customer search",
)

PULL_REQUEST_SECTIONS: tuple[str, ...] = (
    "Summary",
    "Business Purpose",
    "Related Specification",
    "Affected Modules",
    "Testing Result",
    "Checklist",
)

MERGE_STRATEGY = "Squash and Merge"

MERGE_STRATEGY_REASONS: tuple[str, ...] = (
    "Clean history",
    "One feature = one commit",
    "Easier rollback",
    "Simpler release notes",
)

SEMVER_FORMAT = "Major.Minor.Patch"

SEMVER_DEFINITIONS: dict[str, str] = {
    "major": "Breaking architectural changes",
    "minor": "New approved functionality",
    "patch": "Bug fixes only",
}

RELEASE_LIFECYCLE: tuple[str, ...] = (
    "Feature Development",
    "Develop",
    "Release Branch",
    "QA",
    "Approval",
    "Production",
    "Tag",
    "Maintenance",
)

TAG_FORMAT = "v{Major}.{Minor}.{Patch}"

TAG_EXAMPLES: tuple[str, ...] = ("v1.0.0", "v1.0.1", "v1.1.0")

RELEASE_NOTES_SECTIONS: tuple[str, ...] = (
    "Version",
    "Release Date",
    "Summary",
    "Features",
    "Bug Fixes",
    "Database Changes",
    "API Changes",
    "Known Issues",
    "Documentation Updates",
)

ROLLBACK_TRIGGERS: tuple[str, ...] = (
    "Critical bug",
    "Production outage",
    "Security issue",
    "Database corruption",
)

ROLLBACK_PROCESS: tuple[str, ...] = (
    "Identify Release",
    "Checkout Previous Tag",
    "Deploy Previous Image",
    "Restore Database (if required)",
    "Validate",
    "Incident Report",
)

DOCUMENTATION_SYNC_REQUIREMENTS: tuple[str, ...] = (
    "Relevant Volume",
    "Metadata Repository",
    "API Documentation",
    "Database Documentation",
    "README (if applicable)",
)

CI_PULL_REQUEST_CHECKS: tuple[str, ...] = (
    "Build",
    "Lint",
    "Unit Tests",
    "Integration Tests",
    "API Validation",
    "Security Scan",
)

CD_PIPELINE_STAGES: tuple[str, ...] = (
    "Git Push",
    "CI Build",
    "Tests",
    "Docker Image",
    "QA",
    "Approval",
    "Production Deployment",
)

CODE_OWNERSHIP: tuple[dict, ...] = (
    {"module": "Upload", "owner": "Backend Team"},
    {"module": "Intelligence", "owner": "AI Team"},
    {"module": "Dashboard", "owner": "Frontend Team"},
    {"module": "Campaign", "owner": "Marketing Platform Team"},
    {"module": "Provider", "owner": "Integration Team"},
    {"module": "Database", "owner": "Database Team"},
    {"module": "Infrastructure", "owner": "DevOps Team"},
)

REPOSITORY_STANDARDS: tuple[str, ...] = (
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "docs/",
    "metadata/",
    "deployment/",
    ".env.example",
    ".gitignore",
)

DEFINITION_OF_DONE: tuple[str, ...] = (
    "Code implemented",
    "Unit tests pass",
    "Integration tests pass",
    "Documentation updated",
    "Metadata updated",
    "API updated",
    "QA approved",
    "Pull Request approved",
    "Successfully merged into develop",
)

GIT_WORKFLOW_ACCEPTANCE_CRITERIA: tuple[str, ...] = (
    "Branch strategy is standardized",
    "Commit messages follow convention",
    "Pull Requests follow review process",
    "Releases follow semantic versioning",
    "CI/CD pipeline validates changes",
    "Documentation stays synchronized",
    "Production releases are tagged",
    "Rollback process is documented",
    "Cursor-generated commits follow the same workflow",
)
