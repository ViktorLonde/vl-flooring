-- Tabela de preços por serviço (Work Type) e ligação invoice ↔ dias de
-- trabalho. ENTITY_TYPE 'Default' (ENTITY_ID 0) = preço padrão para todos;
-- 'Contractor' / 'Company' = preço combinado com aquele pagador.

CREATE TABLE IF NOT EXISTS service_rates (
  ID INT AUTO_INCREMENT PRIMARY KEY,
  WORK_TYPE_ID INT NOT NULL,
  ENTITY_TYPE ENUM('Default','Contractor','Company','Client') NOT NULL DEFAULT 'Default',
  ENTITY_ID INT NOT NULL DEFAULT 0,
  RATE DECIMAL(10,2) NOT NULL DEFAULT 0,
  UPDATED_AT TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uq_rate (WORK_TYPE_ID, ENTITY_TYPE, ENTITY_ID),
  CONSTRAINT fk_rate_wt FOREIGN KEY (WORK_TYPE_ID) REFERENCES work_types (ID) ON DELETE CASCADE
);

-- Quais dias entraram em cada invoice (gravado ao gerar o invoice).
CREATE TABLE IF NOT EXISTS invoice_work_days (
  INVOICE_TYPE ENUM('Contractor','Company','Client') NOT NULL,
  INVOICE_ID INT NOT NULL,
  WORK_DAY_ID INT NOT NULL,
  PRIMARY KEY (INVOICE_TYPE, INVOICE_ID, WORK_DAY_ID),
  KEY idx_iwd_day (WORK_DAY_ID),
  CONSTRAINT fk_iwd_day FOREIGN KEY (WORK_DAY_ID) REFERENCES work_days (ID) ON DELETE CASCADE
);

-- Invoices antigos: liga pelos mesmos critérios usados ao gerar (entidade + período)
INSERT IGNORE INTO invoice_work_days (INVOICE_TYPE, INVOICE_ID, WORK_DAY_ID)
  SELECT 'Contractor', i.ID, wd.ID FROM contractor_invoices i
  JOIN work_days wd ON wd.CONTRACTOR_ID = i.CONTRACTOR_ID AND wd.WORK_DATE BETWEEN i.PERIOD_FROM AND i.PERIOD_TO
  WHERE i.JOBS_TOTAL > 0;
INSERT IGNORE INTO invoice_work_days (INVOICE_TYPE, INVOICE_ID, WORK_DAY_ID)
  SELECT 'Company', i.ID, wd.ID FROM company_invoices i
  JOIN work_days wd ON wd.COMPANY_ID = i.COMPANY_ID AND wd.WORK_DATE BETWEEN i.PERIOD_FROM AND i.PERIOD_TO
  WHERE i.JOBS_TOTAL > 0;
INSERT IGNORE INTO invoice_work_days (INVOICE_TYPE, INVOICE_ID, WORK_DAY_ID)
  SELECT 'Client', i.ID, wd.ID FROM client_invoices i
  JOIN work_days wd ON wd.CLIENT_ID = i.CLIENT_ID AND wd.WORK_DATE BETWEEN i.PERIOD_FROM AND i.PERIOD_TO
  WHERE i.JOBS_TOTAL > 0;
