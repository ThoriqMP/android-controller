"""
scaffold.py - Project Scaffolding Engine
Buat project baru dengan template dan bantuan AI
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Optional

from ui.tui import (
    menu, prompt, confirm, success, error, info, warn,
    Spinner, section_header, step, print_box
)
from ui.colors import C, colorize


# ============================================================
# TEMPLATE DEFINITIONS
# ============================================================

FRAMEWORKS = {
    "python": {
        "label": "Python — Script / CLI tool",
        "deps": [],
        "files": {
            "main.py": 'def main():\n    print("Hello from {name}!")\n\nif __name__ == "__main__":\n    main()\n',
            "requirements.txt": "",
            ".gitignore": "__pycache__/\n*.pyc\n.env\nvenv/\n",
            "README.md": "# {name}\n\nProject Python baru.\n\n## Cara menjalankan\n\n```bash\npython main.py\n```\n",
        }
    },
    "fastapi": {
        "label": "FastAPI — REST API backend",
        "deps": ["fastapi", "uvicorn[standard]", "python-dotenv"],
        "files": {
            "main.py": (
                "from fastapi import FastAPI\n\napp = FastAPI(title=\"{name}\")\n\n"
                "@app.get(\"/\")\ndef root():\n    return {{\"message\": \"Hello from {name}!\"}}\n\n"
                "@app.get(\"/health\")\ndef health():\n    return {{\"status\": \"ok\"}}\n"
            ),
            "requirements.txt": "fastapi\nuvicorn[standard]\npython-dotenv\n",
            ".env": "APP_HOST=0.0.0.0\nAPP_PORT=8000\n",
            ".gitignore": "__pycache__/\n*.pyc\n.env\nvenv/\n",
            "README.md": (
                "# {name}\n\nFastAPI REST API.\n\n"
                "## Jalankan\n\n```bash\npip install -r requirements.txt\nuvicorn main:app --reload\n```\n\n"
                "## Docs\n\nBuka: http://localhost:8000/docs\n"
            ),
        }
    },
    "flask": {
        "label": "Flask — Lightweight web app",
        "deps": ["flask", "python-dotenv"],
        "files": {
            "app.py": (
                "from flask import Flask\n\napp = Flask(__name__)\n\n"
                "@app.route(\"/\")\ndef index():\n    return \"<h1>Hello from {name}!</h1>\"\n\n"
                "if __name__ == \"__main__\":\n    app.run(debug=True)\n"
            ),
            "requirements.txt": "flask\npython-dotenv\n",
            ".gitignore": "__pycache__/\n*.pyc\n.env\nvenv/\ninstance/\n",
            "README.md": "# {name}\n\nFlask web app.\n\n## Jalankan\n\n```bash\npip install -r requirements.txt\npython app.py\n```\n",
        }
    },
    "nodejs": {
        "label": "Node.js — JavaScript backend",
        "deps": [],
        "files": {
            "index.js": "const http = require('http');\n\nconst PORT = process.env.PORT || 3000;\n\nconst server = http.createServer((req, res) => {{\n  res.writeHead(200, {{ 'Content-Type': 'text/plain' }});\n  res.end('Hello from {name}!\\n');\n}});\n\nserver.listen(PORT, () => console.log(`Server berjalan di http://localhost:${{PORT}}`));\n",
            "package.json": '{{\n  "name": "{name_lower}",\n  "version": "1.0.0",\n  "description": "Node.js project",\n  "main": "index.js",\n  "scripts": {{\n    "start": "node index.js",\n    "dev": "nodemon index.js"\n  }}\n}}\n',
            ".gitignore": "node_modules/\n.env\n",
            "README.md": "# {name}\n\nNode.js app.\n\n## Jalankan\n\n```bash\nnode index.js\n```\n",
        }
    },
    "express": {
        "label": "Express.js — Node.js REST API",
        "deps_npm": ["express", "dotenv"],
        "files": {
            "index.js": (
                "const express = require('express');\nconst app = express();\n"
                "const PORT = process.env.PORT || 3000;\n\n"
                "app.use(express.json());\n\n"
                "app.get('/', (req, res) => res.json({{ message: 'Hello from {name}!' }}));\n\n"
                "app.listen(PORT, () => console.log(`🚀 Server berjalan di http://localhost:${{PORT}}`));\n"
            ),
            "package.json": '{{\n  "name": "{name_lower}",\n  "version": "1.0.0",\n  "main": "index.js",\n  "scripts": {{\n    "start": "node index.js",\n    "dev": "nodemon index.js"\n  }},\n  "dependencies": {{\n    "express": "^4.18.0",\n    "dotenv": "^16.0.0"\n  }}\n}}\n',
            ".gitignore": "node_modules/\n.env\n",
            "README.md": "# {name}\n\nExpress.js REST API.\n\n## Jalankan\n\n```bash\nnpm install\nnpm run dev\n```\n",
        }
    },
    "react": {
        "label": "React — Frontend (Vite)",
        "deps_npm_init": True,
        "files": {}  # dibuat via create-vite
    },
    "nextjs": {
        "label": "Next.js — Full-stack React",
        "deps_npm_init": True,
        "files": {}  # dibuat via create-next-app
    },
}


# ============================================================
# SCAFFOLD ENGINE
# ============================================================

class ScaffoldEngine:
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir).expanduser().resolve()
    
    def _resolve_project_dir(self, name: str) -> Path:
        return self.base_dir / name
    
    def _write_files(self, project_dir: Path, files: dict, name: str):
        """Tulis semua file template ke project dir."""
        for filename, content in files.items():
            filepath = project_dir / filename
            filepath.parent.mkdir(parents=True, exist_ok=True)
            text = content.format(
                name=name,
                name_lower=name.lower().replace(" ", "-")
            )
            filepath.write_text(text, encoding="utf-8")
    
    def _install_python_deps(self, project_dir: Path, deps: list[str]):
        """Install Python dependencies menggunakan pip."""
        if not deps:
            return
        info(f"Menginstall dependencies: {', '.join(deps)}")
        cmd = ["pip", "install"] + deps
        result = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
        if result.returncode == 0:
            success("Dependencies terinstall")
        else:
            warn(f"Gagal install deps: {result.stderr[:200]}")
    
    def _run_npm_init(self, project_dir: Path, framework: str, name: str):
        """Inisialisasi project Node/React/Next via npx."""
        cmds = {
            "react":  ["npx", "-y", "create-vite@latest", str(project_dir), "--template", "react", "--", "--yes"],
            "nextjs": ["npx", "-y", "create-next-app@latest", str(project_dir), "--yes", "--js"],
        }
        if framework not in cmds:
            return
        
        cmd = cmds[framework]
        info(f"Menjalankan: {' '.join(cmd[:4])}...")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=False,
                text=True,
                timeout=300
            )
            if result.returncode != 0:
                warn("Inisialisasi framework mungkin tidak sempurna, cek output di atas.")
        except subprocess.TimeoutExpired:
            warn("Timeout saat inisialisasi. Coba jalankan manual.")
        except FileNotFoundError:
            warn("npx tidak ditemukan. Pastikan Node.js terinstall.")
    
    def scaffold(self, name: str, framework: str) -> Path:
        """
        Buat project baru.
        Returns: Path ke project directory.
        """
        project_dir = self._resolve_project_dir(name)
        template = FRAMEWORKS.get(framework, {})
        
        # Buat direktori
        project_dir.mkdir(parents=True, exist_ok=True)
        
        total_steps = 3
        step(1, total_steps, f"Membuat direktori: {project_dir}")
        
        # Untuk framework yang pakai npx
        if template.get("deps_npm_init"):
            step(2, total_steps, f"Inisialisasi {framework}...")
            self._run_npm_init(project_dir, framework, name)
        else:
            step(2, total_steps, "Menulis file template...")
            self._write_files(project_dir, template.get("files", {}), name)
            
            # Install Python deps
            if template.get("deps"):
                self._install_python_deps(project_dir, template["deps"])
            
            # Install npm deps
            if template.get("deps_npm"):
                (project_dir / "package.json").touch()
                subprocess.run(
                    ["npm", "install"] + template["deps_npm"],
                    cwd=project_dir,
                    capture_output=True
                )
        
        step(3, total_steps, "Finalisasi project...")
        # Buat folder dasar
        (project_dir / ".agents").mkdir(exist_ok=True)
        
        return project_dir


# ============================================================
# INTERACTIVE FLOW
# ============================================================

def run_scaffold():
    """Entry point interaktif untuk `actl new`."""
    section_header("🏗️  BUAT PROJECT BARU", C.BRIGHT_GREEN)
    
    # 1. Pilih framework
    fw_keys  = list(FRAMEWORKS.keys())
    fw_labels = [FRAMEWORKS[k]["label"] for k in fw_keys]
    
    choice = menu("Pilih bahasa / framework:", fw_labels, C.BRIGHT_GREEN)
    if choice == -1:
        info("Dibatalkan.")
        return
    
    framework = fw_keys[choice]
    
    # 2. Nama project
    name = prompt("Nama project", default=f"my-{framework}-app")
    if not name:
        error("Nama project tidak boleh kosong.")
        return
    
    # 3. Lokasi
    base = prompt("Simpan di folder", default="~/projects")
    base_dir = os.path.expanduser(base)
    
    # 4. Konfirmasi
    project_path = os.path.join(base_dir, name)
    print()
    print_box(
        "📋 Ringkasan Project",
        f"Nama      : {name}\n"
        f"Framework : {FRAMEWORKS[framework]['label']}\n"
        f"Lokasi    : {project_path}",
        color=C.BRIGHT_GREEN
    )
    
    if not confirm("Lanjutkan?"):
        info("Dibatalkan.")
        return
    
    # 5. Scaffold
    print()
    engine = ScaffoldEngine(base_dir=base_dir)
    
    with Spinner(f"Membuat project {name}..."):
        pass  # Spinner hanya untuk efek visual di langkah ini
    
    try:
        project_dir = engine.scaffold(name, framework)
        print()
        success(f"Project berhasil dibuat di: {project_dir}")
        
        # 6. Tawarkan AI assistance
        from agent import quick_task
        if confirm("Minta AI untuk membuat README yang lebih lengkap?"):
            ai_readme = quick_task(
                f"Buat README.md yang lengkap dan profesional untuk project {framework} bernama '{name}'. "
                f"Sertakan: deskripsi singkat, instalasi, penggunaan, struktur folder, dan kontribusi. "
                f"Dalam Bahasa Indonesia."
            )
            readme_path = project_dir / "README.md"
            readme_path.write_text(ai_readme, encoding="utf-8")
            success("README diperbarui oleh AI!")
        
        info(f"Masuk ke project: cd {project_dir}")
        
    except Exception as e:
        error(f"Gagal membuat project: {e}")
