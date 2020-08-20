import json
import os
from distutils.util import strtobool

import jq

from utils import (BASE, create_comment, delete_comments, json_from_file,
                   request, validate_file)

team_slug = os.getenv('INPUT_APPROVER_TEAM_SLUG')
path_pattern = os.getenv('INPUT_PATH_PATTERN')
send_comment = strtobool(os.getenv('INPUT_SEND_COMMENT'))
clear_comments = strtobool(os.getenv('INPUT_CLEAR_COMMENTS'))

event_path = os.getenv('GITHUB_EVENT_PATH')
repo = os.getenv('GITHUB_REPOSITORY')
org = repo.split('/')[0]

PR_FILES = BASE + '/repos/{repo}/pulls/{pull_number}/files'
PR_REVIEWS = BASE + '/repos/{repo}/pulls/{pull_number}/reviews'
TEAM_MEMBERSHIP = BASE + '/orgs/{org}/teams/{team_slug}/memberships/{username}'

event = json_from_file(event_path)
pull_number = jq.compile('.pull_request.number').input(event).first()

pr_files_url = PR_FILES.format(repo=repo, pull_number=pull_number)
pr_reviews_url = PR_REVIEWS.format(repo=repo, pull_number=pull_number)
pr_reviews = request('get', pr_reviews_url)
pr_files = request('get', pr_files_url)

approvals = []
errors = []

reviews = jq \
    .compile('[.[] | {user: .user.login, state}] | group_by(.user)[] | last') \
    .input(pr_reviews) \
    .all()

for review in reviews:
    if review['state'] == 'APPROVED':
        username = review['user']
        user_team_url = TEAM_MEMBERSHIP.format(
            org=org, team_slug=team_slug, username=username)

        try:
            team_response = request('get', user_team_url)
            print('team_response')
            print(team_response)
            if team_response['state'] == 'active':
                approvals.append(username)
        except Exception as e:
            # not a team member, skip
            continue

print('=== Validating reviews for files with the following pattern ===')
print('=== {} ==='.format(path_pattern))

for pr_file in pr_files:
    filename = pr_file['filename']
    validation_errors = validate_file(
        path_pattern, filename, approvals, team_slug)

    if len(validation_errors):
        errors.append({
            'path': filename,
            'errors': validation_errors
        })

if clear_comments:
    delete_comments(repo, pull_number)

if len(errors):
    if send_comment:
        create_comment(repo, pull_number, errors)

    for error in errors:
        print(error)

    raise Exception('Fail validation')
