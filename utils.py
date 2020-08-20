import json
import os
import re

import jq
import requests

BASE = os.getenv('GITHUB_API_URL')
ISSUE_COMMENTS = BASE + '/repos/{repo}/issues/{issue_number}/comments'
DELETE_ISSUE_COMMENTS = BASE + '/repos/{repo}/issues/comments/{comment_id}'
AUTHENTICATED_USER = BASE + '/user'

COMMENT_HEADER = '**PR review failed for `{path}`**'
COMMENT = '**Message:** {message}'


def request(verb, url, data=None):
    headers = {'Authorization': 'token {}'.format(os.getenv('INPUT_TOKEN'))}
    verb_map = {
        'get': requests.get,
        'post': requests.post,
        'delete': requests.delete
    }

    response = verb_map.get(verb)(url, json=data, headers=headers)

    if response.status_code >= 200 and response.status_code < 300:
        try:
            return response.json()
        except Exception:
            return response.content
    else:
        raise Exception('Status code {}: {}'.format(response.status_code, url))


def json_from_file(file_path):
    with open(file_path) as f:
        return json.load(f)


def validate_file(path_pattern, file_path, approvals, team_slug):
    pattern = re.compile(path_pattern)
    if pattern.match(file_path):
        if len(approvals) == 0:
            print('INVALID: {}'.format(file_path))
            return [
                {
                    'message': 'It has NOT been approved by `{}` team member'.format(team_slug)
                }
            ]
        else:
            print('VALID: {}'.format(file_path))
            return []
    else:
        print('SKIPPED: {}'.format(file_path))
        return []


def delete_comment(repo, id):
    print('deleting comment {}'.format(id))
    delete_comment_url = DELETE_ISSUE_COMMENTS.format(repo=repo, comment_id=id)
    request('delete', delete_comment_url)


def delete_comments(repo, pull_number):
    print('clearing comments')
    user = request('get', AUTHENTICATED_USER)
    username = jq.compile('.login').input(user).first()

    comment_url = ISSUE_COMMENTS.format(repo=repo, issue_number=pull_number)
    comment_response = request('get', comment_url)
    comments = jq \
        .compile('.[] | {user: .user.login, id, body}') \
        .input(comment_response) \
        .all()

    header_sub = COMMENT_HEADER[:10]
    pattern = re.compile('^{}'.format(re.escape(header_sub)))

    for comment in comments:
        if comment['user'] == username and pattern.match(comment['body']):
            delete_comment(repo, comment['id'])


def create_comment(repo, pull_number, validation_errors):
    print('sending comment')
    formatted_errors = []
    for file in validation_errors:
        path = file['path']
        errors = file['errors']

        header = COMMENT_HEADER.format(path=path)
        error_comment = []
        error_comment.append(header)

        for error in errors:
            message = error['message']

            formatted = COMMENT.format(message=message)
            error_comment.append(formatted)

        the_comment = '\r\n'.join(error_comment)
        formatted_errors.append(the_comment)

    joined_errors = '\r\n\r\n---\r\n'.join(formatted_errors)

    comment_url = ISSUE_COMMENTS.format(repo=repo, issue_number=pull_number)
    body = {'body': joined_errors}
    request('post', comment_url, body)
