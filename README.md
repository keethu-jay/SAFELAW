# SAFELAW
Skill-Augmenting Framework for Enhanced Legal Analysis &amp; Writing  
This tool combines the logic behind CorpusStudios and GP-TSM (Grammar-Preserving Text Saliency Modulation) to create a tool that supports current workflows in the legal field. This tool is being made as a Major Qualifying Project at Worcester Polytechnic Institute by Brett Gerlach, Keerthana Jayamoorthy, and Julian Mariscal under the guidance of Professor Erin Solovey at WPI and Chelse Swoopes, PhD Candidate at Harvard University.

## Repository Layout
- `frontend/` – Vite + React client, Tailwind + Material UI styling
- `backend/` – data prep, server sources, and scripts
- `References/` – supporting documentation for CorpusStudios, GP-TSM

## Frontend
### Tools Used
- `React` – component framework for building the pages.
- `TypeScript` – typed authoring for React components and helpers.
- `Vite` – dev server and bundler for fast HMR builds.
- `React Router` – handles public routes plus shared layout wrapping.
- `Tailwind CSS` – utility classes for spacing, typography, and background styling.
- `Material UI` – provides the layout panels, Paper, Box, Stack, and Buttons that shape the mockup-inspired UI.
- `ESLint` – keeps the TypeScript/React codebase linted through `npm run lint`.

## Backend
### Tools Used

### Running the Frontend
```bash
cd frontend
npm install
npm run dev
```
