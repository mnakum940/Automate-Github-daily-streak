import os
from dotenv import load_dotenv
from github import Github, GithubException

# Load environment explicitly
load_dotenv()

token = os.getenv("GITHUB_TOKEN")
if not token:
    print("❌ ERROR: GITHUB_TOKEN not found in environment variables.")
    exit(1)

print(f"Token loaded: {token[:4]}...{token[-4:]}")

try:
    g = Github(token)
    user = g.get_user()
    print(f"[OK] Authenticated as: {user.login}")
    
    # Test repo creation permission
    print("Testing repository creation permission...")
    repo_name = "test-repo-permission-check"
    try:
        repo = user.create_repo(repo_name, description="Test repo for permission check", private=True)
        print("[OK] SUCCESS: Repository created successfully.")
        repo.delete()
        print("[OK] SUCCESS: Repository deleted successfully.")
    except GithubException as e:
        print(f"[FAIL] FAILED to create repository: {e.status} {e.data['message']}")
        print("   -> Your token lacks the 'repo' scope.")

except GithubException as e:
    print(f"[FAIL] Authentication Failed: {e.status} {e.data['message']}")
