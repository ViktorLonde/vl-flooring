-- Diária do helper (pagamento = diária × parte do dia) e rateio de uma
-- despesa entre vários Job Codes (ex.: gasolina da semana).
-- helpers.DAILY_RATE é adicionado pelo script em Python (sem IF NOT EXISTS no MySQL):
-- ALTER TABLE helpers ADD COLUMN DAILY_RATE DECIMAL(10,2) DEFAULT NULL;
CREATE TABLE IF NOT EXISTS expense_allocations (
  ID INT AUTO_INCREMENT PRIMARY KEY,
  EXPENSE_ID INT NOT NULL,
  JOB_PROJECT_ID INT NOT NULL,
  AMOUNT DECIMAL(10,2) NOT NULL,
  KEY idx_alloc_exp (EXPENSE_ID),
  CONSTRAINT fk_alloc_exp FOREIGN KEY (EXPENSE_ID) REFERENCES expenses (ID) ON DELETE CASCADE,
  CONSTRAINT fk_alloc_job FOREIGN KEY (JOB_PROJECT_ID) REFERENCES job_projects (ID) ON DELETE CASCADE
);
