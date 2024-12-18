"""Fill in a module description here"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/01_utils.ipynb.

# %% auto 0
__all__ = ['trace_exception', 'clone_repo']

# %% ../nbs/01_utils.ipynb 3
import os, git
import traceback

def trace_exception(e):
    """Trace and print the exception details"""
    print(f"An error occurred: {e}")
    print("Traceback details:")
    traceback.print_exc()  # Print detailed traceback

def clone_repo(
    repo_url:str, 
    target_dir:str, 
    auth_token:str=None
):
    """Clone a Git repository to the target directory with optional authentication."""
    try:
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        # If an authentication token is provided, use it
        if auth_token:
            repo_url_with_token = repo_url.replace("https://", f"https://{auth_token}@")
        else:
            repo_url_with_token = repo_url

        git.Repo.clone_from(repo_url_with_token, target_dir)
    except Exception as e:
        print(f"Failed to clone the repository: {e}")
