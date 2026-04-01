import sys
import os
import json
import uuid

# Works both locally (from repo root) and in Lambda
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)
))))

from github import Github, GithubException
from .template import generate_pr_body


def lambda_handler(event, context=None):
    """
    PR Generator Lambda Handler.
    Creates a GitHub Pull Request with the approved security patch.
    """
    try:
        # Extract input fields
        repo_full_name = event.get("repo_full_name", "")
        file_path = event.get("file_path", "")
        final_patch = event.get("final_patch", "")
        vulnerability_type = event.get("vulnerability_type", "")
        cwe = event.get("cwe", "")
        severity = event.get("severity", "")
        exploit_evidence = event.get("exploit_evidence", "")
        changes_made = event.get("changes_made", [])

        # Validate required fields
        if not all([repo_full_name, file_path, final_patch]):
            return {
                "status": "ERROR",
                "pr_url": "",
                "branch_name": "",
                "error_message": "Missing required fields: repo_full_name, file_path, final_patch"
            }

        # Fetch GitHub token from environment
        github_token = os.environ.get("GITHUB_TOKEN")
        if not github_token:
            return {
                "status": "ERROR",
                "pr_url": "",
                "branch_name": "",
                "error_message": "GITHUB_TOKEN environment variable not set"
            }

        # Initialize GitHub client
        g = Github(github_token)

        # Get the repository
        repo = g.get_repo(repo_full_name)

        # Get the default branch (usually main or master)
        default_branch = repo.default_branch
        main_ref = repo.get_git_ref(f"heads/{default_branch}")
        main_sha = main_ref.object.sha

        # Generate unique branch name
        branch_name = f"patchops-fix-{uuid.uuid4().hex[:8]}"

        # Create new branch from main
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_sha)

        # Get the current file's SHA (required for update_file)
        file_contents = repo.get_contents(file_path, ref=default_branch)
        current_file_sha = file_contents.sha

        # Update the file on the new branch with the patched code
        commit_message = f"Auto-patch: Fix {vulnerability_type}"
        repo.update_file(
            path=file_path,
            message=commit_message,
            content=final_patch,
            sha=current_file_sha,
            branch=branch_name
        )

        # Generate the PR body markdown
        pr_body = generate_pr_body(
            vulnerability_type=vulnerability_type,
            cwe=cwe,
            severity=severity,
            exploit_evidence=exploit_evidence,
            changes_made_list=changes_made
        )

        # Create the Pull Request
        pr = repo.create_pull(
            title=f"🔒 Security Patch: {vulnerability_type}",
            body=pr_body,
            head=branch_name,
            base=default_branch
        )

        # Return success response
        return {
            "status": "SUCCESS",
            "pr_url": pr.html_url,
            "branch_name": branch_name
        }

    except GithubException as e:
        # Handle GitHub API errors gracefully
        error_msg = f"GitHub API error: {str(e)}"
        print(f"ERROR: {error_msg}")
        return {
            "status": "ERROR",
            "pr_url": "",
            "branch_name": "",
            "error_message": error_msg
        }

    except Exception as e:
        # Handle any other unexpected errors
        error_msg = f"PR generation exception: {str(e)}"
        print(f"ERROR: {error_msg}")
        return {
            "status": "ERROR",
            "pr_url": "",
            "branch_name": "",
            "error_message": error_msg
        }
