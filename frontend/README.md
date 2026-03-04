# SafeLaw Frontend

Overview of the frontend app: structure, tech stack, theme, layout, and auth.

---

## What's in the Frontend

- **Pages**: Home, Login, Writer, Reader, Profile
- **Layout**: Shared header + footer wrapping all routes; main content area uses React Router `Outlet`
- **Auth**: Supabase email/password; `AuthContext` exposes `user`, `login`, `logout` to the app
- **Data**: Supabase client (`supabaseClient.ts`) for auth and backend API calls

---

## Technologies

| Technology | Purpose |
|------------|---------|
| **React 19** | UI components and state |
| **TypeScript** | Typed JS for components and logic |
| **Vite** | Dev server, HMR, production build |
| **React Router DOM** | Client-side routing |
| **Tailwind CSS** | Utility classes for spacing, layout, responsive |
| **Material UI (MUI)** | Components (Box, CircularProgress, etc.), icons |
| **Emotion** | CSS-in-JS used by MUI |
| **Supabase** | Auth (email/password) and backend API client |

---

## Style Libraries

- **Tailwind CSS** – Utility-first CSS for layout, margins, padding, responsive breakpoints
- **Material UI** – Layout primitives (Box, Paper), form controls, icons (`@mui/icons-material`)
- **styleguide.css** – Design tokens: colors, fonts, similarity pills, button styles
- **index.css** – Base styles, font imports (Lexend, Merriweather, Open Sans), Tailwind directives

---

## Theme and Layout

### Theme

- **Background**: Deep blue-black (`#091325`) for main UI; warm off-white (`#F5F2EF`) for editor/text areas
- **Text**: Light gray (`#C5D2DE`) on dark; dark gray (`#333333`) on light
- **Accents**: Teal (`#008C99`) primary, copper (`#C4623C`) secondary; WCAG AA compliant
- **Font**: Lexend for headings and body; Merriweather/Open Sans for specific content
- **Similarity pills**: Color-coded (red → orange → yellow → green) for relevance scores

### Layout

- **Header**: Logo, nav (Workspace when logged in, Login when not), profile icon
- **Main**: Full-width content area with padding; `Outlet` renders the active route
- **Footer**: Copyright
- **Structure**: `Layout` wraps all routes; `min-height: 100vh`, flex column, sticky header/footer

---

## Pages (5)

| Route | Page | Description |
|-------|------|-------------|
| `/` | Home | Landing: hero, Writing Tool / Reader links |
| `/login` | Login | Email/password form; redirects to Profile on success |
| `/writer` | Writer | Drafting workspace with RAG suggestions |
| `/reader` | Reader | Structured reading mode for case text |
| `/profile` | Profile | User profile (post-login destination) |

---

## Auth

- **Provider**: Supabase Auth (email + password)
- **Client**: `@supabase/supabase-js`; env vars `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`
- **Context**: `AuthContext` wraps the app; `useAuth()` returns `user`, `loading`, `login`, `logout`
- **Session**: `supabase.auth.getSession()` on load; `onAuthStateChange` keeps state in sync
- **UI**: Header shows Workspace + profile icon when logged in; Login link when not

---

## Scripts

```bash
npm run dev      # Start dev server (Vite)
npm run build    # TypeScript check + production build
npm run lint     # ESLint
npm run preview  # Preview production build
```
