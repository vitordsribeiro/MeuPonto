# Registrador de Ponto

Esqueleto do projeto — as rotas e templates já estão prontos, faltam as
funções de lógica (marcadas com `TODO` e `raise NotImplementedError`).

## Ordem sugerida para implementar

1. **services/sheets.py** → `find_user_by_email`, `find_user_by_id`
2. **auth.py** → `verify_login` (depende do passo 1)
3. **services/horas.py** → `calcular_horas_dia`, `calcular_horas_mes`
4. **services/sheets.py** → `get_today_record`, `get_month_records`
5. **services/sheets.py** → `registrar_ponto` (a mais importante — o "bater o ponto" em si)
6. **services/sheets.py** → `editar_registro`

Assim você primeiro faz o login funcionar, depois o cálculo de horas
(que é Python puro, sem depender da planilha), e só por último a escrita
na planilha, que é a parte mais nova para você.

## Setup local

```bash
python -m venv venv
source venv/bin/activate  # no Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Criar a Service Account do Google

1. Acesse https://console.cloud.google.com
2. Crie um projeto (ou use um existente)
3. Ative a **Google Sheets API**
4. Vá em "Credenciais" → "Criar credenciais" → "Conta de serviço"
5. Depois de criada, gere uma chave em formato JSON e baixe
6. Renomeie o arquivo para `credentials.json` e coloque na raiz do projeto
   (esse arquivo é sensível — não vai pro Git! já está no .gitignore)
7. Copie o "email" da service account (algo como `xxx@xxx.iam.gserviceaccount.com`)
8. Crie sua planilha no Google Sheets, com as abas `Usuarios` e `RegistrosPonto`
   (veja o formato esperado no topo de `services/sheets.py`)
9. Compartilhe a planilha com o email da service account, como **Editor**
10. Copie o ID da planilha (fica na URL, entre `/d/` e `/edit`) e cole em
    `SHEET_ID` dentro de `services/sheets.py`

### Rodar localmente

```bash
python app.py
```

Acesse http://localhost:5000

## Próximos passos (depois que tudo estiver funcionando local)

- Trocar a `secret_key` fixa por variável de ambiente
- Trocar `credentials.json` local por variável de ambiente também
  (necessário para hospedar no Vercel, que não guarda arquivos)
- Criar o `vercel.json` apontando pro `app.py` como função Python
