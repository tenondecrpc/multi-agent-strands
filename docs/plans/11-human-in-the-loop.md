# 10. Human-in-the-Loop: Review and CI/CD

Generated code by agents **never goes directly to production**. The approval flow:

```
Agents generate code
       ↓
Git branch: agent/proj-123
       ↓
Automatic Pull Request (GitHub/CodeCommit)
       ↓
CI/CD Pipeline activates:
  ├── Linting (ruff, eslint)
  ├── Unit tests (pytest, vitest)
  ├── Integration tests
  ├── Security scan (bandit, npm audit)
  └── Build check
       ↓
  ┌─────────────────────────┐
  │  HUMAN REVIEW REQUIRED  │
  │                         │
  │  - PR code review       │
  │  - Verify quality       │
  │  - Approve or reject    │
  └─────────────────────────┘
       ↓ (if approved)
  Merge → Deploy to staging → Deploy to prod
```

## Branch Protection Configuration

```yaml
# GitHub branch protection (configure via UI or API)
branch_protection:
  required_reviews: 1
  dismiss_stale_reviews: true
  require_code_owner_reviews: true
  required_status_checks:
    - lint
    - test-backend
    - test-frontend
    - security-scan
```

## Generic CI/CD (CodeBuild/GitHub Actions)

```yaml
# buildspec.yml for CodeBuild / .github/workflows/ci.yml
version: 0.2
phases:
  install:
    commands:
      - pip install -r requirements.txt
      - npm ci
  build:
    commands:
      - ruff check .
      - pytest tests/ --tb=short
      - cd frontend && npm run lint && npm run test
  post_build:
    commands:
      - echo "All checks passed — awaiting human review"
```
