# HavoSec authentication

Roles are centralized in `utils/roles.py`: `superadmin`, `admin`, and `user`.
Legacy `super_admin`, `viewer`, and `client` values are normalized without elevating access.
All authenticated accounts are stored in the single `users` collection.

Access tokens are one-hour Bearer JWTs by default. Configure `JWT_SECRET` and optionally
`ACCESS_TOKEN_MINUTES`. Configure allowed frontend origins with comma-separated
`CORS_ORIGINS`.

## First superadmin

Set `SUPERADMIN_EMAIL` and a `SUPERADMIN_PASSWORD` of at least 12 characters, then run:

```powershell
backend\venv\Scripts\python.exe backend\bootstrap_superadmin.py
```

The command is idempotent and never changes an existing account password. Demo accounts
are disabled by default; `SEED_DEMO_ACCOUNTS=true` is for explicit local development only.

## Legacy account migration

After taking a MongoDB backup, run `backend\venv\Scripts\python.exe backend\migrate_auth_accounts.py`
once. It is idempotent, normalizes legacy role names and account statuses, and never
promotes an account to superadmin.

Password-reset and verification tokens are stored as SHA-256 hashes and are not returned
by default. A real email sender should deliver generated links. For isolated local testing
only, `AUTH_EXPOSE_TEST_TOKENS=true` returns the link (never enable it in production).
