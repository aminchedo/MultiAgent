# Frontend Guide – MultiAgent Vibe Coding Platform

This guide explains the structure, purpose, and navigation of the **frontend** codebase.  
It is designed so that any developer can quickly understand where each page and script belongs.

---

## 📂 File Structure

- **enhanced_vibe_frontend.html**
  - The **Main Dashboard** of the platform.
  - Used to submit prompts, track agent status, and download generated project files.
  - Includes UI panels for:
    - Agent monitoring (Planner, Coder, Critic, FileManager, Orchestrator)
    - Job submission and progress
    - File listing and download

- **test_vibe_integration.html**
  - Lightweight **API testing page**.
  - Used to verify backend endpoints (`/api/vibe-coding`, `/status`, `/files`) are working.
  - Developers should use this first if there are API connection issues.

- **assets/**
  - Contains CSS styles, fonts, and images.
  - Any UI-specific design should be added here.

- **components/**
  - (Optional future expansion) Split UI parts into reusable HTML/JS components:
    - StatusPanel
    - FileList
    - ProgressTracker

---

## 🚀 Development Workflow

1. **Always start from `enhanced_vibe_frontend.html`**
   - This is the main entry point for the user-facing frontend.
   - All integration with backend APIs happens here.

2. **Use `test_vibe_integration.html` for quick debugging**
   - If you suspect API or connection problems, test endpoints here before touching the main dashboard.

3. **Frontend logic**
   - JavaScript logic is embedded inside `<script>` tags in each HTML file.
   - Styles are either inline `<style>` blocks or external files inside `assets/`.

---

## 📌 Notes for Developers
- Do not duplicate API logic between pages — keep `test_vibe_integration.html` minimal and for debugging only.
- Always verify new features against the orchestrator workflow (`/api/vibe-coding`).
- Keep UI components simple and modular — if expanded, place them under `components/`.