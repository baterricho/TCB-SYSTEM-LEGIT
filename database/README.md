# The Creator's Bulwark Database SQL

This folder contains PostgreSQL/Supabase SQL scripts for The Creator's Bulwark backend.

The scripts are based on the current Django models and initial migrations in this project. They are intended as a database schema backup/reference and as preparation material for Supabase PostgreSQL.

These files do not automatically create database tables. They only run if you manually paste them into Supabase SQL Editor or execute them through a SQL tool.

## Recommended Workflow

Use Django as the source of truth:

1. Django models
2. Django migrations
3. Supabase PostgreSQL as the database host

Django should connect to Supabase through the `.env` database connection string.

## Alternative Workflow

If you intentionally want to create the schema manually:

1. Open Supabase Dashboard
2. Go to SQL Editor
3. Create a New Query
4. Paste `database/full_schema.sql`
5. Click Run

Only use this path when the SQL still matches the current Django models and migrations.

## Important Warning

Do not run both a manual SQL schema and Django migrations if they create duplicate or conflicting tables.

If Django migrations are your source of truth, do not manually run the SQL unless you have verified that it matches the models exactly. The `django_migrations` recorder table is managed by Django and is intentionally not populated by these scripts.

## File Order

Run the files in this order if you do not use `full_schema.sql`:

1. `001_extensions_and_enums.sql`
2. `002_tables.sql`
3. `003_indexes_and_constraints.sql`
4. `004_rls_policies.sql`
5. `005_reference_data.sql`
6. `006_views_and_functions.sql`

`full_schema.sql` combines the same SQL into one runnable script.

## Supabase Auth Note

The current backend uses Django authentication and SimpleJWT. Supabase is only the PostgreSQL database host unless the application is later changed to use Supabase Auth.

The RLS file includes policies that map a Supabase authenticated user's email claim to `public."user".email`. Those policies are useful only if Supabase Auth is used, or if equivalent JWT context is passed to PostgreSQL. When Django connects directly with its database connection string, Django's API permissions remain the primary authorization layer.

## Verify Tables After Manual Run

Use this query in Supabase SQL Editor:

```sql
select table_name
from information_schema.tables
where table_schema = 'public'
order by table_name;
```
