import os

# Project name
PROJECT_NAME = "ai_fact_checker"

# Folder structure
structure = {
    PROJECT_NAME: [
        "requirements.txt",
        "Dockerfile",
        ".env",
        ".gitignore",
        ".dockerignore",
        "README.md",

        # Backend
        "app/__init__.py",
        "app/main.py",
        "app/routes.py",
        "app/workflow.py",
        "app/prompts.py",
        "app/models.py",
        "app/utils.py",
        "app/sse.py",

        # Frontend
        "frontend/index.html",
        "frontend/style.css",

        # CI/CD
        ".github/workflows/deploy.yml",

        # AWS configs (optional placeholders)
        "infra/docker-compose.yml",
        "infra/nginx.conf",
    ]
}

def create_structure(base_path, files):
    for file in files:
        file_path = os.path.join(base_path, file)

        # Create directory if not exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Create empty file if not exists
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                pass

if __name__ == "__main__":
    for folder, files in structure.items():
        create_structure(folder, files)

    print(f"✅ Project '{PROJECT_NAME}' structure created successfully!")