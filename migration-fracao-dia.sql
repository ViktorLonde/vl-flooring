-- Parte do dia trabalhada (1 = dia inteiro, 0.5 = meio dia, 0.333 = 1/3…)
-- no dia de trabalho e por helper. Rodado pelo script Python (o MySQL não
-- aceita ADD COLUMN IF NOT EXISTS — confira com SHOW COLUMNS antes).
ALTER TABLE work_days ADD COLUMN DAY_FRACTION DECIMAL(5,3) NOT NULL DEFAULT 1.000;
ALTER TABLE work_day_helpers ADD COLUMN DAY_FRACTION DECIMAL(5,3) NOT NULL DEFAULT 1.000;
