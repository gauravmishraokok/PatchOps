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
    Creates a GitHub Pull Request with the approved security patches.
    """
    try:
        # Extract input fields
        repo_full_name = event.get("repo_full_name", "")
        file_path = event.get("file_path", "")
        final_patch = event.get("final_patch", "")
        fixed_vulnerabilities = event.get("fixed_vulnerabilities", [])
        
        # NEW: Extra audit results
        req_check_result = event.get("req_check_result")
        test_results = event.get("test_results", [])

        print(f"PR_GENERATOR: Targeting repo {repo_full_name}, file {file_path}")

        # Validate required fields
        if not all([repo_full_name, file_path, final_patch]):
            return {
                "status": "ERROR",
                "pr_url": "",
                "branch_name": "",
                "error_message": f"Missing required fields. Received: repo={repo_full_name}, path={file_path}"
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
        try:
            repo = g.get_repo(repo_full_name)
        except GithubException as ge:
            if ge.status == 404:
                return {"status": "ERROR", "error_message": f"Repository '{repo_full_name}' not found. Check name and token permissions."}
            raise ge

        # Get the default branch
        default_branch = repo.default_branch
        main_ref = repo.get_git_ref(f"heads/{default_branch}")
        main_sha = main_ref.object.sha

        # Generate unique branch name
        branch_name = f"patchops-fix-{uuid.uuid4().hex[:8]}"

        # Create new branch from main
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_sha)

        # Get the current file's SHA
        try:
            file_contents = repo.get_contents(file_path, ref=default_branch)
            current_file_sha = file_contents.sha
        except GithubException as ge:
            if ge.status == 404:
                return {"status": "ERROR", "error_message": f"File '{file_path}' not found in repo '{repo_full_name}'."}
            raise ge

        # Update the file
        vulnerability_summary = f"{len(fixed_vulnerabilities)} vulnerabilities" if fixed_vulnerabilities else "security fixes"
        commit_message = f"Auto-patch: Fix {vulnerability_summary}"
        repo.update_file(
            path=file_path,
            message=commit_message,
            content=final_patch,
            sha=current_file_sha,
            branch=branch_name
        )

        # Generate the PR body markdown - PASS NEW RESULTS
        pr_body = generate_pr_body(
            fixed_vulnerabilities_list=fixed_vulnerabilities,
            req_check_result=req_check_result,
            test_results=test_results
        )

        # Create the Pull Request title
        pr_title = "🔒 Security Patch: Autonomous Remediation & Verification"
        if fixed_vulnerabilities and fixed_vulnerabilities[0].get('vulnerability_type') != "Dependency Consistency Fix":
             pr_title = f"🔒 Security Patch: {len(fixed_vulnerabilities)} Vulnerabilities Fixed"

        # Create the Pull Request
        pr = repo.create_pull(
            title=pr_title,
            body=pr_body,
            head=branch_name,
            base=default_branch
        )

        return {
            "status": "SUCCESS",
            "pr_url": pr.html_url,
            "branch_name": branch_name
        }

    except GithubException as e:
        error_msg = f"GitHub API error: {e.status} {e.data.get('message', str(e))}"
        return {"status": "ERROR", "pr_url": "", "branch_name": "", "error_message": error_msg}

    except Exception as e:
        error_msg = f"PR generation exception: {str(e)}"
        return {"status": "ERROR", "pr_url": "", "branch_name": "", "error_message": error_msg}
