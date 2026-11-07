-- ============================================================
-- Job Site Inbox — histórico de endereços por data (job_site_visits)
--
-- Rode no MESMO banco que o app usa de verdade
-- (192.168.4.34 / bd_vl_flooring). Só cria uma tabela nova — sem
-- nenhuma mudança em tabela existente.
-- ============================================================

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

    -- 'EMAIL' por enquanto (só existe essa origem) — deixa a coluna
    -- pronta caso um dia surja outra forma de capturar o endereço.
    SOURCE          VARCHAR(20) NOT NULL DEFAULT 'EMAIL',
    EMAIL_SUBJECT   VARCHAR(255),

    CREATED_AT      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_job_site_visits_project (JOB_PROJECT_ID),
    INDEX idx_job_site_visits_date (VISIT_DATE)
);
