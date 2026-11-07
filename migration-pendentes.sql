-- ============================================================
-- Migrações pendentes: Job Site Inbox (histórico) + Helpers
--
-- Rode tudo de uma vez, de cima a baixo, no banco real
-- (192.168.4.34 / bd_vl_flooring). Se sua versão do MySQL for anterior
-- à 8.0.29, ela não suporta "ADD COLUMN IF NOT EXISTS" — nesse caso,
-- rode os dois ALTER TABLE do final sem o "IF NOT EXISTS"; se der erro
-- de coluna já existente, pode ignorar com segurança.
-- ============================================================

-- ------------------------------------------------------------
-- 1) Job Site Inbox — histórico de endereços por data
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS job_site_visits (
    ID              INT AUTO_INCREMENT PRIMARY KEY,
    JOB_PROJECT_ID  INT NOT NULL,

    -- Data do endereço confirmado: usa a data do próprio e-mail (quando dá
    -- pra ler o cabeçalho Date), senão cai no dia em que você aplicou aqui
    -- no app.
    VISIT_DATE      DATE NOT NULL,

    JOB_ADDRESS     VARCHAR(200) NOT NULL,
    JOB_ADDRESS2    VARCHAR(100),
    CITY_ID         INT NULL,
    STATE_ID        INT NULL,
    ZIP_CODE        VARCHAR(15),

    SOURCE          VARCHAR(20) NOT NULL DEFAULT 'EMAIL',
    EMAIL_SUBJECT   VARCHAR(255),

    CREATED_AT      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_job_site_visits_project (JOB_PROJECT_ID),
    INDEX idx_job_site_visits_date (VISIT_DATE)
);

-- ------------------------------------------------------------
-- 2) Helpers — cadastro de ajudantes de obra
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS helpers (
    ID            INT AUTO_INCREMENT PRIMARY KEY,
    FULL_NAME     VARCHAR(150) NOT NULL,
    COMPANY_NAME  VARCHAR(150),
    EMAIL         VARCHAR(150),
    PHONE_NUMBER  VARCHAR(30),
    PHONE_NUMBER2 VARCHAR(30),
    ADDRESS       VARCHAR(200),
    ADDRESS2      VARCHAR(100),
    CITY_ID       INT NULL,
    STATE_ID      INT NULL,
    ZIP_CODE      VARCHAR(15),
    CREATED_AT    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_helpers_full_name (FULL_NAME)
);

-- ------------------------------------------------------------
-- 3) Vínculo do Helper com o Job (work_days) e o snapshot do
--    projeto (job_projects)
-- ------------------------------------------------------------
ALTER TABLE work_days ADD COLUMN IF NOT EXISTS HELPER_ID INT NULL;
ALTER TABLE job_projects ADD COLUMN IF NOT EXISTS HELPER_ID INT NULL;
