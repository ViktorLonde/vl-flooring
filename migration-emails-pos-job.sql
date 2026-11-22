-- Melhorias de 21/11/2026 (e-mails, estoque mínimo, follow-ups).
-- Aplicado por aplicar_migracao_2111.py (checa SHOW COLUMNS antes — o MySQL 8.0.46
-- daqui não aceita ADD COLUMN IF NOT EXISTS). Backup feito antes.

-- Estimate por e-mail: quando foi enviado
ALTER TABLE estimates ADD COLUMN SENT_AT DATETIME NULL;

-- Avisos de Compliance: para qual vencimento já mandou o aviso de 30 e de 7 dias
ALTER TABLE compliance_items ADD COLUMN REMINDED_30_FOR DATE NULL;
ALTER TABLE compliance_items ADD COLUMN REMINDED_7_FOR DATE NULL;

-- Estoque mínimo por produto (0 = sem alerta)
ALTER TABLE products ADD COLUMN MIN_STOCK DECIMAL(10,2) NOT NULL DEFAULT 0;

-- Follow-ups depois do job (30 dias: avaliação; 1 ano: garantia)
CREATE TABLE IF NOT EXISTS job_followups (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    JOB_PROJECT_ID INT NOT NULL,
    KIND VARCHAR(20) NOT NULL,           -- REVIEW_30 | WARRANTY_1Y
    RESULT VARCHAR(20) NOT NULL,         -- SENT | DONE | SKIPPED
    NOTE VARCHAR(255) NULL,
    DONE_AT DATETIME NOT NULL,
    UNIQUE KEY uq_followup (JOB_PROJECT_ID, KIND),
    CONSTRAINT fk_followup_project FOREIGN KEY (JOB_PROJECT_ID) REFERENCES job_projects (ID) ON DELETE CASCADE
);
