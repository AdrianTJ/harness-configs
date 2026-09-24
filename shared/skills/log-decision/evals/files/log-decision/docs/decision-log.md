# Decision log

## DEC-007: Use PostgreSQL for the pilot
- **Date:** 2026-08-14
- **Status:** decided
- **Context:** The team needed durable reporting and structured queries before the pilot launch.
- **Options considered:** Managed PostgreSQL added operational cost; SQLite was simpler but made concurrent reporting fragile.
- **Decision:** Use managed PostgreSQL for the pilot.
- **Consequences:** Reporting depends on the managed database and requires migration planning if the pilot expands.
