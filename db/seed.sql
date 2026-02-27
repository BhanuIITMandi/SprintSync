-- ============================================================
-- SEED DATA — Demo users and tasks for SprintSync
-- Runs after schema.sql on first docker-compose up
-- ============================================================

-- Reset existing data (redundant if using docker-compose down -v, but safe)
TRUNCATE tasks, users RESTART IDENTITY CASCADE;

-- Demo users with specific domains
-- Passwords: user1, user2, user3, user4, user5
INSERT INTO users (email, hashed_password, skills, is_admin) VALUES
  ('user1@example.com', '$2b$12$Diedf86U2OwJ6OCOwHBeNuI6BV4aIyC4atAhY3ME4/v9iKe09WYNK', 'data science, machine learning, python, pandas, pytorch', FALSE),
  ('user2@example.com', '$2b$12$xOqLUrcGmehLITZRpnjQ6O5IoObhG1uhqVZ.rD/aQ6Cm1SHUZGirK', 'sde, software development, java, spring boot, react, microservices', FALSE),
  ('user3@example.com', '$2b$12$PQ1EZBl58IWbThCMkA3gtuc68x26Ht8o5G1HQ2zBWW21lvLA2nqKe', 'data engineering, spark, hadoop, sql, etl, airflow', FALSE),
  ('user4@example.com', '$2b$12$Cciwhcl8uuhGub.x6ulZN.47E.raBOAh1qbK2DZ/b2cloXUz6Y.1a', 'devops, docker, kubernetes, terraform, aws, ci/cd', FALSE),
  ('user5@example.com', '$2b$12$8/q8Rmf4SSlStGd2BU7ReeSws176zsmWtGRzE3EfLN7DscNLwA7HW', 'qa, testing, selenium, cypress, automation, quality assurance', FALSE)
ON CONFLICT (email) DO NOTHING;

-- Assign 5 tasks to each user
-- User 1 (DS)
INSERT INTO tasks (title, description, status, total_minutes, user_id, assigned_to) VALUES
  ('Train Model v1', 'Train the first iteration of the forecasting model.', 'IN_PROGRESS', 120, 1, 1),
  ('Data Cleaning', 'Clean the raw telemetry data for modeling.', 'DONE', 180, 1, 1),
  ('Analyze Results', 'Evaluate model performance on test set.', 'TODO', 0, 1, 1),
  ('Feature Engineering', 'Extract new temporal features from logs.', 'TODO', 0, 1, 1),
  ('Optimize Hyperparameters', 'Fine-tune the XGBoost parameters.', 'TODO', 0, 1, 1);

-- User 2 (SDE)
INSERT INTO tasks (title, description, status, total_minutes, user_id, assigned_to) VALUES
  ('Build API Gateway', 'Implement the central routing for microservices.', 'IN_PROGRESS', 240, 2, 2),
  ('Fix React Bug', 'Resolve the race condition in the dashboard layout.', 'DONE', 60, 2, 2),
  ('Implement Auth', 'Add JWT login and register endpoints.', 'TODO', 0, 2, 2),
  ('Write Unit Tests', 'Test the core business logic in the service layer.', 'TODO', 0, 2, 2),
  ('Setup Redis Caching', 'Improve performance for frequently accessed items.', 'TODO', 0, 2, 2);

-- User 3 (DE)
INSERT INTO tasks (title, description, status, total_minutes, user_id, assigned_to) VALUES
  ('Setup Airflow DAGs', 'Schedule daily ingestion from S3 to Redshift.', 'IN_PROGRESS', 150, 3, 3),
  ('Optimize SQL Query', 'Refactor the heavy join query for better speed.', 'DONE', 45, 3, 3),
  ('Data Migration', 'Move data from legacy MySQL to Postgres.', 'TODO', 0, 3, 3),
  ('Build CDC Pipeline', 'Implement change data capture for real-time sync.', 'TODO', 0, 3, 3),
  ('Monitoring Dashboard', 'Create alerts for pipeline failures.', 'TODO', 0, 3, 3);

-- User 4 (DevOps)
INSERT INTO tasks (title, description, status, total_minutes, user_id, assigned_to) VALUES
  ('K8s Cluster Upgrade', 'Upgrade the EKS nodes to latest version.', 'IN_PROGRESS', 300, 4, 4),
  ('Terraform Provisioning', 'Infrastructure as Code for staging environment.', 'DONE', 120, 4, 4),
  ('Secret Management', 'Implement Vault for secure credential storage.', 'TODO', 0, 4, 4),
  ('Configure ArgoCD', 'Setup GitOps for automatic deployments.', 'TODO', 0, 4, 4),
  ('Log Aggregation', 'Deploy ELK stack for centralized logging.', 'TODO', 0, 4, 4);

-- User 5 (QA)
INSERT INTO tasks (title, description, status, total_minutes, user_id, assigned_to) VALUES
  ('Automation Regression', 'Run selenium tests for the latest release.', 'IN_PROGRESS', 90, 5, 5),
  ('Write Test Plan', 'Define test cases for the new billing module.', 'DONE', 60, 5, 5),
  ('Performance Testing', 'Load test the API under high concurrency.', 'TODO', 0, 5, 5),
  ('Security Audit', 'Check for common OWASP vulnerabilities.', 'TODO', 0, 5, 5),
  ('Verify Bug Fixes', 'Manual testing of the reported UI issues.', 'TODO', 0, 5, 5);
