# Database Migrations with Alembic (Future)

This guide explains how to set up Alembic for database migrations when you're ready to version-control your schema changes.

## Current State

Right now, the application uses `init_db()` which calls:

```python
await conn.run_sync(Base.metadata.create_all)
```

This automatically creates tables on startup if they don't exist. This works great for:
- ✅ Initial development
- ✅ Simple deployments
- ✅ Getting started quickly

However, for production and team environments, you'll want:
- Version-controlled schema changes
- Rollback capability
- Team collaboration on schema
- Audit trail of changes

That's where **Alembic** comes in.

## When to Migrate to Alembic

Consider switching to Alembic when:

1. **Multiple developers** working on database schema
2. **Production deployment** requiring controlled migrations
3. **Schema changes** becoming frequent
4. **Need to rollback** a migration
5. **Audit requirements** for schema changes

## Setting Up Alembic

### 1. Initialize Alembic

```bash
cd backend
uv run alembic init alembic
```

This creates:
```
backend/
├── alembic/
│   ├── env.py           # Alembic configuration
│   ├── script.py.mako   # Migration template
│   └── versions/        # Migration scripts
└── alembic.ini          # Alembic settings
```

### 2. Configure Alembic

Edit `alembic.ini`:

```ini
# Replace this line:
sqlalchemy.url = driver://user:pass@localhost/dbname

# With:
# sqlalchemy.url =  # Leave empty, we'll use env.py
```

Edit `alembic/env.py`:

```python
from app.db.base import Base
from app.core.config import get_settings

# Add this at the top
settings = get_settings()

# Replace the target_metadata line:
target_metadata = Base.metadata

# Update the configuration section:
def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = settings.database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    from sqlalchemy import pool
    from sqlalchemy.ext.asyncio import create_async_engine

    connectable = create_async_engine(
        settings.database_url,
        poolclass=pool.NullPool,
    )

    async def do_migrations():
        async with connectable.connect() as connection:
            await connection.run_sync(do_sync_migrations)

    def do_sync_migrations(connection):
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()

    import asyncio
    asyncio.run(do_migrations())
```

### 3. Import All Models

In `alembic/env.py`, add after the Base import:

```python
from app.db.base import Base
from app.db.models import ChatModel, MessageModel  # Import all models
```

This ensures Alembic sees all your models.

### 4. Create Initial Migration

Generate migration from current models:

```bash
uv run alembic revision --autogenerate -m "Initial schema"
```

This creates `alembic/versions/xxxx_initial_schema.py` with:
- `upgrade()`: Creates tables
- `downgrade()`: Drops tables

Review the generated file!

### 5. Apply Migration

```bash
uv run alembic upgrade head
```

This runs all pending migrations.

### 6. Update Application Code

In `app/main.py`, replace:

```python
# OLD
await init_db()
```

With:

```python
# NEW - Let Alembic handle schema
# Just verify connection
async with engine.connect() as conn:
    logger.info("Database connection established")
```

Or keep both for backwards compatibility:

```python
# For local dev: auto-create tables
if settings.debug:
    await init_db()
else:
    # Production: require explicit migrations
    logger.info("Migrations must be run manually with 'alembic upgrade head'")
```

## Common Alembic Commands

### Create New Migration

After modifying models:

```bash
# Auto-generate migration
uv run alembic revision --autogenerate -m "Add user_id to chats"

# Or create empty migration to write manually
uv run alembic revision -m "Custom migration"
```

### Apply Migrations

```bash
# Upgrade to latest
uv run alembic upgrade head

# Upgrade one version
uv run alembic upgrade +1

# Upgrade to specific version
uv run alembic upgrade abc123
```

### Rollback Migrations

```bash
# Downgrade one version
uv run alembic downgrade -1

# Downgrade to specific version
uv run alembic downgrade abc123

# Downgrade all (back to empty DB)
uv run alembic downgrade base
```

### Check Status

```bash
# Show current version
uv run alembic current

# Show migration history
uv run alembic history

# Show pending migrations
uv run alembic heads
```

## Example: Adding a New Column

### 1. Update Model

In `app/db/models.py`:

```python
class ChatModel(Base):
    # ... existing fields ...
    
    # Add new field
    last_read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

### 2. Generate Migration

```bash
uv run alembic revision --autogenerate -m "Add last_read_at to chats"
```

### 3. Review Migration

Check `alembic/versions/xxxx_add_last_read_at.py`:

```python
def upgrade() -> None:
    op.add_column('chats', sa.Column('last_read_at', sa.DateTime(), nullable=True))

def downgrade() -> None:
    op.drop_column('chats', 'last_read_at')
```

### 4. Apply Migration

```bash
uv run alembic upgrade head
```

## Example: Complex Migration (Data Transform)

Sometimes you need to transform existing data:

```python
def upgrade() -> None:
    # Add new column
    op.add_column('messages', sa.Column('text_length', sa.Integer(), nullable=True))
    
    # Populate it from existing data
    op.execute("""
        UPDATE messages
        SET text_length = LENGTH(text)
        WHERE text IS NOT NULL
    """)
    
    # Make it non-nullable
    op.alter_column('messages', 'text_length', nullable=False)

def downgrade() -> None:
    op.drop_column('messages', 'text_length')
```

## Production Deployment Workflow

### Development

```bash
# 1. Modify models
# 2. Generate migration
uv run alembic revision --autogenerate -m "Description"
# 3. Review and edit migration
# 4. Test migration
uv run alembic upgrade head
# 5. Commit migration file to git
git add alembic/versions/*.py
git commit -m "Add migration: description"
```

### Staging/Production

```bash
# 1. Pull latest code
git pull

# 2. Check pending migrations
uv run alembic current
uv run alembic heads

# 3. Backup database (important!)
pg_dump -U user setdm_db > backup_$(date +%Y%m%d).sql

# 4. Apply migrations
uv run alembic upgrade head

# 5. Start application
uvicorn app.main:app
```

## Migration Best Practices

### ✅ DO

1. **Review auto-generated migrations** - Alembic might not catch everything
2. **Test migrations** - Apply and rollback in development
3. **Keep migrations small** - One logical change per migration
4. **Add data migrations carefully** - Consider large tables
5. **Backup before applying** - Always in production
6. **Version control migrations** - Commit to git
7. **Document complex migrations** - Add comments
8. **Test downgrades** - Ensure rollback works

### ❌ DON'T

1. **Don't edit applied migrations** - Create a new one instead
2. **Don't skip versions** - Apply in order
3. **Don't auto-generate without review** - Check the SQL
4. **Don't forget nullable columns** - Consider existing data
5. **Don't rush production migrations** - Test thoroughly
6. **Don't ignore warnings** - Alembic tells you issues
7. **Don't delete old migrations** - Needed for rollback
8. **Don't modify Base.metadata directly in production** - Use migrations

## Handling Conflicts

If two developers create migrations simultaneously:

```bash
# You'll see:
# Multiple head revisions are present
# abc123 (head)
# def456 (head)

# Merge them:
uv run alembic merge -m "Merge heads" abc123 def456

# This creates a new migration that references both
# Apply it:
uv run alembic upgrade head
```

## Troubleshooting

### Migration Detects No Changes

**Problem**: `alembic revision --autogenerate` creates empty migration

**Solutions**:
1. Ensure models are imported in `alembic/env.py`
2. Check `target_metadata` points to `Base.metadata`
3. Restart your shell to reload Python modules

### "Can't locate revision" Error

**Problem**: Migration references unknown revision

**Solutions**:
1. Ensure all migrations are in `alembic/versions/`
2. Check `alembic_version` table in database
3. Reset if needed: `alembic stamp head`

### Database Out of Sync

**Problem**: Manual changes made to database

**Solutions**:
1. **Option 1**: Rollback manual changes
2. **Option 2**: Create migration matching current state
3. **Option 3**: Reset and reapply:
   ```bash
   alembic downgrade base
   alembic upgrade head
   ```

## Converting Existing Database

If you already have data in the database:

```bash
# 1. Backup
pg_dump -U user setdm_db > backup.sql

# 2. Initialize Alembic
uv run alembic init alembic

# 3. Configure (see above)

# 4. Stamp current state (don't create tables)
uv run alembic stamp head

# 5. Now you're ready for future migrations
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Run Migrations

on:
  push:
    branches: [main]

jobs:
  migrate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Install dependencies
        run: uv sync
      
      - name: Check migrations
        run: |
          uv run alembic check
          uv run alembic upgrade head
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

## Summary

**Current Setup (Simple)**:
- ✅ Auto-creates tables on startup
- ✅ Easy for development
- ❌ No version control
- ❌ No rollback capability

**With Alembic (Professional)**:
- ✅ Version-controlled migrations
- ✅ Rollback capability
- ✅ Team collaboration
- ✅ Audit trail
- ⚠️ Requires more setup

**Recommendation**: Start with current setup, migrate to Alembic when:
- Going to production
- Multiple developers
- Schema changes become frequent

---

**Resources**:
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 2.0 Alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html#running-our-first-migration)
- [Alembic Cookbook](https://alembic.sqlalchemy.org/en/latest/cookbook.html)

