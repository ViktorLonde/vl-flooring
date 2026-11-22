# Ideias para as próximas melhorias (salvas em 20/11/2026)

Agora que o e-mail funciona:

1. **Estimate por e-mail** — botão "Send by e-mail" no orçamento: manda o PDF para o cliente com mensagem pronta; o estimate vira SENT e guarda a data de envio.
2. **Agenda da semana para cada helper** — o "Share week" manda para cada helper só os dias e endereços dele, por e-mail (toda sexta ou num clique).
3. **Recibo de pagamento automático** — ao registrar um pagamento num invoice, o app oferece mandar "Payment received, thank you" com valor, data e quanto ainda falta.
4. **Extrato mensal por cliente (Statement)** — PDF com todos os invoices em aberto de uma empresa/contractor, com quanto está atrasado (30/60/90 dias); dá para mandar todo dia 1º.
5. **Aviso de vencimentos por e-mail** — seguro, licença e outros itens de Compliance: e-mail 30 e 7 dias antes de vencer.

Sugestão: começar pela 3 e pela 4 (ajudam a receber mais rápido).

Pendente do lado do usuário: **dados do banco** em Settings (aparecem nos invoices).

**Atualização 20/11/2026 (noite):** o Viktor pediu para continuar guardando estas ideias — ainda não começadas.
Já feito desde então: Settings em abas (Company/Invoices/Email/System), detalhe de cada forma de pagamento (Zelle, Venmo, Cash App, PayPal…) com prévia da invoice, e o app sempre abre na Home.
Também pendente: Job Code e quantidade dos materiais #22–#25 (e Bostik GreenForce #16).

---

# Novas ideias (20/11/2026, noite) — continuar amanhã

## Etapa 1 — Registrar o dia de trabalho por e-mail (começar por esta)
- No celular: e-mail para a conta de Settings → Email, **assunto** `dia JB-0032`, texto opcional `meio dia, Juan e Pedro`.
- No app: tela nova **Work Day Inbox** → Check Inbox → mostra "20/11 · JB-0032 (cliente, endereço) · meio dia · Juan, Pedro" → [Confirmar] [Editar] [Ignorar].
- Ao confirmar, cria o dia igual ao "Log today": copia do último dia do Job Code o cliente, endereço, serviços e equipe; valor pelos Service Rates.
- Data = data do e-mail (aceitar `ontem` ou `19/11`). Sem texto = dia inteiro e mesma equipe. `dia JB-0032 JB-0035` = dois jobs, meio dia cada. Avisar se o Job Code não existe ou se já tem dia nessa data (não duplicar).

## Etapa 2 — Lançar material usado por e-mail
- No celular: **assunto** `material JB-0032`, uma linha por material (`6 Bostik SL-100`, `2 ProFlex primer`, `12 caixas Bone`), foto da nota opcional.
- No app: tela **Material Inbox** → reconhece cada linha no cadastro de Products (partes do nome, marca, código como NEWRSV111) → tabela com ✅/⚠️ para conferir → **Lançar no job**.
- Produto não encontrado → botão para cadastrar na hora. Foto da nota fica guardada (depois pode virar Purchase). Sem preço entra $0, como hoje.

## Outras ideias novas
3. Preço por SF de cada job (receita e material por pé quadrado, por tipo de serviço).
4. Sugestão de preço no Estimate com base em jobs parecidos.
5. Previsão de caixa (invoices em aberto, pagamento de helpers, compras).
6. Reserva de imposto trimestral com aviso antes das datas do IRS (só referência; confirmar com o contador).
7. Acompanhamento pós-job (30 dias: avaliação/indicação; 1 ano: garantia).
8. PDF de entrega com checklist e assinatura do cliente.
9. Aviso de estoque baixo no "Needs your attention".

## Pendências
- Commit das mudanças de 20/11 (abas do Settings, formas de pagamento com prévia, abrir sempre na Home) — ainda não feito. Antes, colocar `receipts_received/` no `.gitignore` (fotos de recibos).
- Do Viktor: Service Rates, preço dos materiais em $0, cadastro de helpers, dados bancários, Job Code e quantidade dos materiais #22–#25 (e #16).
