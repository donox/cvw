#!/bin/bash
# Run from /opt/cvwapp on the server
# Stamps the accounts migration and seeds default categories

docker compose exec web bash -c "cd /app && alembic stamp a1b2c3d4e5f6"

  cat > /tmp/seed_accounts.py << 'PYEOF'
import app.models.member, app.models.user, app.models.officer, app.models.org  # noqa
import app.models.program, app.models.group, app.models.email_models  # noqa
from app.database import SessionLocal
from app.models.financial import AccountCategory

SEED = [
    ('Dues',          'Income',  'Annual membership dues'),
    ('Show Income',   'Income',  'Revenue from wood-turning shows'),
    ('Store Sale',    'Income',  'Store/merchandise sales'),
    ('Donation',      'Income',  'Charitable donations received'),
    ('Other Income',  'Income',  'Miscellaneous income'),
    ('Venue',         'Expense', 'Meeting or event venue costs'),
    ('Supplies',      'Expense', 'Club supplies and consumables'),
    ('Program Cost',  'Expense', 'Speaker fees and program expenses'),
    ('Printing',      'Expense', 'Printing and copying'),
    ('Equipment',     'Expense', 'Tools and equipment purchases'),
    ('Website',       'Expense', 'Hosting and domain costs'),
    ('Other Expense', 'Expense', 'Miscellaneous expenses'),
]
db = SessionLocal()
if db.query(AccountCategory).count() == 0:
    for name, typ, desc in SEED:
        db.add(AccountCategory(name=name, type=typ, description=desc))
    db.commit()
    print(f'Seeded {len(SEED)} categories')
else:
    print('Categories already present, skipping')
db.close()
PYEOF

cat > /tmp/seed_accounts.py << 'EOF'
  import app.models.member, app.models.user, app.models.officer, app.models.org
  import app.models.program, app.models.group, app.models.email_models
  from app.database import SessionLocal
  from app.models.financial import AccountCategory
  SEED = [
      ('Dues','Income','Annual membership dues'),
      ('Show Income','Income','Revenue from wood-turning shows'),
      ('Store Sale','Income','Store/merchandise sales'),
      ('Donation','Income','Charitable donations received'),
      ('Other Income','Income','Miscellaneous income'),
      ('Venue','Expense','Meeting or event venue costs'),
      ('Supplies','Expense','Club supplies and consumables'),
      ('Program Cost','Expense','Speaker fees and program expenses'),
      ('Printing','Expense','Printing and copying'),
      ('Equipment','Expense','Tools and equipment purchases'),
      ('Website','Expense','Hosting and domain costs'),
      ('Other Expense','Expense','Miscellaneous expenses'),
  ]
  db = SessionLocal()
  if db.query(AccountCategory).count() == 0:
      for n,t,d in SEED: db.add(AccountCategory(name=n,type=t,description=d))
      db.commit(); print('Seeded', len(SEED), 'categories')
  else: print('Already seeded, skipping')
  db.close()
  EOF
  docker compose cp /tmp/seed_accounts.py web:/app/seed_accounts.py
  docker compose exec web bash -c "cd /app && python seed_accounts.py"
