import os
import subprocess
import time
import tempfile
import threading
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import requests
import git

load_dotenv()

app = Flask(__name__)

# Load environment variables
SHARED_SECRET = os.getenv("SHARED_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
EVALUATION_URL = os.getenv("EVALUATION_URL")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")

def generate_app_code(brief):
    """
    This function would use an LLM to generate code based on the brief.
    For now, it returns a simple placeholder.
    """
    return f"""
# Auto-generated app based on: {brief}
def main():
    print("Hello from the generated app!")

if __name__ == "__main__":
    main()
"""

@app.route('/api-endpoint', methods=['POST'])
def api_endpoint():
    # Check the secret from header or JSON body
    secret = request.headers.get('X-Secret') or (request.is_json and request.get_json().get('secret'))
    if secret != SHARED_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    # Extract data from the request
    brief = data.get('brief')
    email = data.get('email')
    task = data.get('task')
    round_num = data.get('round')
    nonce = data.get('nonce')

    if not all([brief, email, task, round_num, nonce]):
        return jsonify({"error": "Missing required fields"}), 400

    repo_name = f"app-{task}"
    repo_url = f"https://github.com/{GITHUB_USERNAME}/{repo_name}"

    try:
        # Create a public repository
        subprocess.run(
            ["gh", "repo", "create", repo_name, "--public", f"--token={GITHUB_TOKEN}"],
            check=True, capture_output=True, text=True
        )

        with tempfile.TemporaryDirectory() as repo_path:
            # Clone the newly created repository
            git.Repo.clone_from(repo_url, repo_path, env={"GIT_ASKPASS": "echo", "GIT_USERNAME": GITHUB_USERNAME, "GIT_PASSWORD": GITHUB_TOKEN})

            # Create a minimal app using our placeholder function
            app_code = generate_app_code(brief)
            with open(os.path.join(repo_path, "app.py"), "w") as f:
                f.write(app_code)

            # Add a README.md
            with open(os.path.join(repo_path, "README.md"), "w") as f:
                f.write(f"# {repo_name}\n\nThis repository contains a minimal app for the task: {task}.\n\n## Summary\n\n{brief}\n\n## License\n\nThis project is licensed under the MIT License.\n")

            # Add a LICENSE file
            with open(os.path.join(repo_path, "LICENSE"), "w") as f:
                f.write("MIT License\n\nCopyright (c) 2024\n\nPermission is hereby granted, free of charge, to any person obtaining a copy...")

            # Commit and push the changes
            repo = git.Repo(repo_path)
            repo.git.add(all=True)
            repo.index.commit("Initial commit")
            origin = repo.remote(name="origin")
            origin.push()

            # Enable GitHub Pages
            subprocess.run(
                ["gh", "api", f"repos/{GITHUB_USERNAME}/{repo_name}/pages", "-f", 'source[branch]=main', "-f", 'source[path]=/', f"--token={GITHUB_TOKEN}"],
                check=True, capture_output=True, text=True
            )

            commit_sha = repo.head.commit.hexsha
            pages_url = f"https://{GITHUB_USERNAME}.github.io/{repo_name}/"

            # Notify the evaluation service in a background thread
            notification_payload = {
                "email": email, "task": task, "round": round_num, "nonce": nonce,
                "repo_url": repo_url, "commit_sha": commit_sha, "pages_url": pages_url,
            }
            threading.Thread(target=send_notification, args=(notification_payload,)).start()

            return jsonify({
                "message": "Repository creation and app generation initiated.",
                "repo_url": repo_url,
            }), 202 # Accepted

    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Failed to execute command", "details": e.stderr}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def send_notification(payload):
    delay = 1
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = requests.post(
                EVALUATION_URL, json=payload, headers={"Content-Type": "application/json"}, timeout=10
            )
            response.raise_for_status()
            print("Notification sent successfully.")
            return
        except requests.exceptions.RequestException as e:
            print(f"Failed to send notification (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                print("Max retries reached. Giving up.")

if __name__ == '__main__':
    app.run(debug=True, port=5001)