-- ============================================================
-- SEED DATA — Demo users and tasks for SprintSync
-- Runs after schema.sql on first docker-compose up
-- ============================================================

-- Demo users (passwords are bcrypt-hashed versions of "password123")
INSERT INTO users (email, hashed_password, is_admin) VALUES
  ('admin@sprintsync.io',  '$2b$12$nGkohaB0I7yIKkMVv64oQ.cTmvGb/NkGNoUtC6QV6nPCWS6a0onKG', TRUE),
  ('alice@sprintsync.io',  '$2b$12$nGkohaB0I7yIKkMVv64oQ.cTmvGb/NkGNoUtC6QV6nPCWS6a0onKG', FALSE)
ON CONFLICT (email) DO NOTHING;

-- Demo tasks spanning different statuses
INSERT INTO tasks (title, description, status, total_minutes, user_id) VALUES
  ('Set up CI pipeline',         'Configure GitHub Actions for lint + test + build.',         'DONE',        120, 1),
  ('Design database schema',     'Create ERD and write migration scripts for Postgres.',      'DONE',         90, 1),
  ('Implement auth endpoints',   'JWT-based login and registration with bcrypt hashing.',     'IN_PROGRESS',  60, 2),
  ('Build task CRUD API',        'RESTful endpoints for creating, reading, updating tasks.',  'TODO',          0, 2),
  ('Integrate AI suggestion',    'Wire up /ai/suggest with OpenAI fallback to stub.',         'TODO',          0, 1)
ON CONFLICT DO NOTHING;
