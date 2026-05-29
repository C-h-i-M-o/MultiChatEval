CREATE DATABASE IF NOT EXISTS multichateval CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE multichateval;

CREATE TABLE IF NOT EXISTS users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(64) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversations (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NULL,
  title VARCHAR(120) NOT NULL DEFAULT '新评测会话',
  mode VARCHAR(32) NOT NULL DEFAULT 'compare',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_conversations_user FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS model_providers (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(64) NOT NULL UNIQUE,
  base_url VARCHAR(255) NULL,
  api_key_encrypted VARCHAR(512) NULL,
  enabled BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS model_configs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  provider_id BIGINT NOT NULL,
  model_name VARCHAR(120) NOT NULL,
  display_name VARCHAR(120) NOT NULL,
  price_input DECIMAL(10, 6) NOT NULL DEFAULT 0,
  price_output DECIMAL(10, 6) NOT NULL DEFAULT 0,
  max_tokens INT NOT NULL DEFAULT 4096,
  enabled BOOLEAN NOT NULL DEFAULT TRUE,
  CONSTRAINT fk_model_configs_provider FOREIGN KEY (provider_id) REFERENCES model_providers(id)
);

CREATE TABLE IF NOT EXISTS evaluation_tasks (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  conversation_id BIGINT NULL,
  user_id BIGINT NULL,
  prompt TEXT NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'pending',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  completed_at DATETIME NULL,
  CONSTRAINT fk_evaluation_tasks_conversation FOREIGN KEY (conversation_id) REFERENCES conversations(id),
  CONSTRAINT fk_evaluation_tasks_user FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS model_responses (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  task_id BIGINT NOT NULL,
  model_config_id BIGINT NULL,
  answer_text TEXT NOT NULL,
  latency_ms INT NOT NULL DEFAULT 0,
  input_tokens INT NOT NULL DEFAULT 0,
  output_tokens INT NOT NULL DEFAULT 0,
  estimated_cost DECIMAL(10, 6) NOT NULL DEFAULT 0,
  status VARCHAR(32) NOT NULL DEFAULT 'success',
  error_message TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_model_responses_task FOREIGN KEY (task_id) REFERENCES evaluation_tasks(id),
  CONSTRAINT fk_model_responses_model_config FOREIGN KEY (model_config_id) REFERENCES model_configs(id)
);

CREATE TABLE IF NOT EXISTS evaluation_results (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  response_id BIGINT NOT NULL,
  relevance_score DECIMAL(4, 2) NOT NULL DEFAULT 0,
  completeness_score DECIMAL(4, 2) NOT NULL DEFAULT 0,
  clarity_score DECIMAL(4, 2) NOT NULL DEFAULT 0,
  accuracy_score DECIMAL(4, 2) NOT NULL DEFAULT 0,
  usefulness_score DECIMAL(4, 2) NOT NULL DEFAULT 0,
  objective_score DECIMAL(4, 2) NOT NULL DEFAULT 0,
  rule_score DECIMAL(4, 2) NOT NULL DEFAULT 0,
  judge_score DECIMAL(4, 2) NULL,
  final_score DECIMAL(4, 2) NOT NULL DEFAULT 0,
  judge_comment TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_evaluation_results_response FOREIGN KEY (response_id) REFERENCES model_responses(id)
);

CREATE TABLE IF NOT EXISTS user_feedback (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NULL,
  response_id BIGINT NOT NULL,
  feedback_type VARCHAR(32) NOT NULL,
  comment TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_user_feedback_user FOREIGN KEY (user_id) REFERENCES users(id),
  CONSTRAINT fk_user_feedback_response FOREIGN KEY (response_id) REFERENCES model_responses(id)
);

INSERT INTO model_providers (name, base_url, enabled)
VALUES
  ('deepseek', 'https://api.deepseek.com', TRUE),
  ('qwen', 'https://dashscope.aliyuncs.com/compatible-mode/v1', TRUE),
  ('zhipu', 'https://open.bigmodel.cn/api/paas/v4', TRUE),
  ('openai-compatible', NULL, TRUE)
ON DUPLICATE KEY UPDATE enabled = VALUES(enabled);
