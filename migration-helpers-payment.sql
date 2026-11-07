-- ============================================================
-- Helpers — formas de pagamento (Zelle, Cash App, Venmo, Cheque,
-- Transferência Bancária)
--
-- Rode no MESMO banco que o app usa de verdade
-- (192.168.4.34 / bd_vl_flooring). Só adiciona colunas na tabela
-- `helpers` que já existe — não cria tabela nova.
-- ============================================================

ALTER TABLE helpers ADD COLUMN IF NOT EXISTS PAYMENT_ZELLE VARCHAR(150);
ALTER TABLE helpers ADD COLUMN IF NOT EXISTS PAYMENT_CASHAPP VARCHAR(100);
ALTER TABLE helpers ADD COLUMN IF NOT EXISTS PAYMENT_VENMO VARCHAR(100);
ALTER TABLE helpers ADD COLUMN IF NOT EXISTS PAYMENT_CHECK_NAME VARCHAR(150);
ALTER TABLE helpers ADD COLUMN IF NOT EXISTS PAYMENT_BANK_ROUTING VARCHAR(20);
ALTER TABLE helpers ADD COLUMN IF NOT EXISTS PAYMENT_BANK_ACCOUNT VARCHAR(30);

-- ============================================================
-- NOTA: se sua versão do MySQL for anterior à 8.0.29, ela não suporta
-- "ADD COLUMN IF NOT EXISTS" — nesse caso, rode os ALTER TABLE acima sem
-- o "IF NOT EXISTS"; se der erro de coluna já existente, pode ignorar
-- com segurança.
--
-- NOTA SOBRE DADOS SENSÍVEIS: routing number e account number (conta
-- bancária) são dados mais sensíveis que os outros campos dessa tabela.
-- Ficam guardados como texto simples no banco, igual todo o resto do
-- app — se algum dia esse banco for exposto fora da sua rede local,
-- vale considerar criptografar essas duas colunas especificamente.
-- ============================================================
