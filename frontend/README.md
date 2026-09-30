# JeevanSetu frontend

Next.js 16, React 19, TypeScript, and Tailwind CSS frontend for the JeevanSetu synthetic-data hackathon demo.

Phase 0 contains only the landing page and a live backend/SQLite health indicator. Upload, extraction, conflict, score, and vault interfaces are not implemented yet.

> Synthetic demo data only. Not legal advice.

From this directory:

```bash
npm ci
npm run dev
```

The browser expects the API at `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`). See the repository root `README.md` for Docker Compose and full validation instructions.
