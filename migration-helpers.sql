-- ============================================================
-- Helpers — cadastro de ajudantes de obra + vínculo com o Job
--
-- Rode no MESMO banco que o app usa de verdade
-- (192.168.4.34 / bd_vl_flooring).
-- ============================================================

-- ------------------------------------------------------------
-- 1) HELPERS — mesmo nível de detalhe do Contractor (nome, empresa,
--    contato, endereço). Sem W9/website/redes sociais — isso é só do
--    Contractor (subcontratado 1099), não do Helper.
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
-- 2) work_days ganha HELPER_ID (nullable — Job sem Helper continua
--    normal, é um campo opcional, ao contrário do Contractor).
-- ------------------------------------------------------------
ALTER TABLE work_days ADD COLUMN IF NOT EXISTS HELPER_ID INT NULL;

-- ------------------------------------------------------------
-- 3) job_projects também ganha HELPER_ID — é o mesmo "snapshot" que já
--    guarda CONTRACTOR_ID/CLIENT_ID/etc pra esse projeto.
-- ------------------------------------------------------------
ALTER TABLE job_projects ADD COLUMN IF NOT EXISTS HELPER_ID INT NULL;

-- ============================================================
-- NOTA: se sua versão do MySQL for anterior à 8.0.29, ela não suporta
-- "ADD COLUMN IF NOT EXISTS" — nesse caso, rode os dois ALTER TABLE
-- acima sem o "IF NOT EXISTS"; se der erro de coluna já existente, pode
-- ignorar com segurança.
-- ============================================================
