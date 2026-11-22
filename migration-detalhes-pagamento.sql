-- Detalhe de cada forma de pagamento mostrado na invoice
-- (ex.: {"Zelle": "941-382-7383", "Venmo": "@vertexlonde"}), salvo como JSON.
-- Aplicado em 2026-11-20.
ALTER TABLE app_settings ADD COLUMN PAYMENT_DETAILS TEXT DEFAULT NULL;
