# PR Review Validator

A Github Action to determine whether PR reviews are coming from the correct team

## How to use it?

Create `.github/workflows/<workflow_name>.yml`

```yaml
name: Pull request review workflow
on:
  pull_request_review:
    branches:
      - master
jobs:
  validate_pr_review:
    name: Validate reviews
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate PR review for sink config
        uses: snapcart/pr-review-validator@v1.0.0
        with:
          token: ${{ secrets.USER_TOKEN }}
          approver_team_slug: dwh-engine-admins
          path_pattern: .*sink_(schema|config).json$
          send_comment: true
          clear_comments: true
      - name: Validate PR review for source config
        uses: snapcart/pr-review-validator@v1.0.0
        with:
          token: ${{ secrets.USER_TOKEN }}
          approver_team_slug: dwh-users-snapcart
          path_pattern: .*source_query.(json|sql)$|.*source_config.json$|.*source_mapping.jq$
          send_comment: true
          clear_comments: true
```

Inputs|Required|Default|Description
------|--------|-------|-----------
`token`|Yes|-|GitHub token to access pull request details, comments, and user membership. Need a token which has the following scopes: `read:org`, `repo`
`approver_team_slug`|Yes|-|Only approvals from member of this team are considered as valid
`path_pattern`|Yes|-|Path to evaluated files in RegEx
`send_comment`|No|False|Create a comment containing validation errors
`clear_comments`|No|False|Clear previous error comment(s)