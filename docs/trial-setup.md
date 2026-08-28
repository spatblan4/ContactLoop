# ContactLoop Beta and Demo setup

The repository supports two runtime modes with the same codebase:

- `demo`: the public, login-free hackathon presentation backed by the Demo Supabase data.
- `authenticated`: the private Beta workspace for teachers and real student imports.

The environment label in the app follows the same rule: authenticated is **Beta** and demo is **Demo**.

## Create the trial environment

1. Create a separate Supabase project for trial use.
2. Run `supabase/schema.sql`, then run `supabase/patch-import-students-auth.sql` in that project’s SQL editor.
3. Enable Email / Password under Supabase Authentication.
4. Create a local `.env.local` from `.env.example` with the trial project values:

```bash
VITE_APP_MODE=authenticated
VITE_SUPABASE_URL=https://your-trial-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-trial-anon-key
```

5. Start the Beta app with `npm run dev` (or `npm run dev:beta`) and create the first teacher account from the sign-up screen.

The original roster file is parsed in the browser and is not uploaded or retained. Only confirmed structured rows are sent to the `import_students` RPC. The RPC derives `teacher_id` from `auth.uid()` and writes students and guardians together.

## Keep the hackathon demo separate

Use a separate Demo env file when presenting:

```bash
VITE_APP_MODE=demo
VITE_SUPABASE_URL=https://your-demo-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-demo-anon-key
```

Start it with `npm run dev:demo`.

Do not commit either `.env.local` file. Use separate Supabase projects so demo seed data and trial users never share a database.
