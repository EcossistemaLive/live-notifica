# 📘 Manual de Implantação e Uso do Live Monitor
### Guia Prático Passo a Passo para Escritórios de Advocacia e Consultorias
**Versão:** 1.0 (Edição Comercial) | **Público:** Gestores, Sócios, Advogados e Operadores

---

## 💡 O que é o Live Monitor?

O **Live Monitor** é um assistente digital inteligente criado para escritórios jurídicos e contábeis que cuidam de múltiplos clientes.

Em vez de você ter que entrar todos os dias em dezenas de portais governamentais (Receita Federal, e-CAC, SEFAZ estadual, Prefeituras e Diários de Justiça) ou checar centenas de e-mails espalhados:

1. Os e-mails e avisos oficiais dos seus clientes chegam automaticamente a uma caixa central do seu escritório por **apelidos (aliases)**.
2. O sistema lê as mensagens, identifica de qual empresa cliente se trata e extrai o prazo legal (ex: *"15 dias para responder"*).
3. O robô envia um **alerta executivo no WhatsApp do advogado ou contador responsável**, com o resumo do que precisa ser feito e o PDF da intimação anexado.
4. Tudo fica registrado de forma segura no seu **ClickUp** e em relatórios em conformidade com as regras da **OAB e da LGPD**.

---

## 📋 Lista de Checagem Prévia (O que você precisa ter)

Antes de iniciar a instalação de 1 clique, certifique-se de ter:
- [ ] Um computador ou servidor com Windows, Linux ou Mac conectado à internet.
- [ ] Uma caixa de e-mail própria do escritório (ex: `notificacoes@seuescritorio.com.br` no Google Workspace ou Outlook).
- [ ] Um número de WhatsApp para o robô usar (pode ser o WhatsApp do escritório ou um número exclusivo de atendimento).
- [ ] A lista das empresas que você atende, com os nomes e telefones dos advogados/contadores responsáveis.

---

## 🚀 Passo 1: Instalação Rápida em 1 Clique

Disponibilizamos scripts prontos que preparam todo o ambiente automaticamente:

### No Windows:
1. Abra a pasta `scripts` do projeto.
2. Dê um duplo clique no arquivo:  
   👉 **`instalar_windows.bat`**
3. O instalador vai baixar o navegador seguro e preparar os arquivos de configuração. Quando terminar, aperte qualquer tecla para fechar.

### No Linux ou Servidor em Nuvem:
1. Abra o terminal na pasta do projeto e execute:
   ```bash
   bash scripts/instalar_linux.sh
   ```

---

## 🔑 Passo 2: Configuração da Caixa Central de E-mail

Para que o robô possa ler os e-mails recebidos sem precisar da sua senha pessoal:

1. Abra o arquivo **`.env`** (na raiz da pasta) com o Bloco de Notas.
2. **Defina o nome do seu escritório** na primeira linha:
   ```env
   OFFICE_NAME="Silva & Prado Advogados Associados"
   ```
   *(Esse nome aparecerá no cabeçalho de todas as mensagens de WhatsApp que seus clientes e parceiros receberem).*

3. **Preencha o e-mail central do escritório:**
   ```env
   IMAP_HOST=imap.gmail.com
   IMAP_USER=notificacoes@seuescritorio.com.br
   IMAP_PASSWORD=xxxx xxxx xxxx xxxx
   ```

> 🔒 **Como gerar a "Senha de App" no Gmail / Google Workspace (2 minutos):**
> 1. Acesse sua conta Google em: [https://myaccount.google.com/security](https://myaccount.google.com/security)
> 2. Verifique se a opção *"Verificação em duas etapas"* está ativada.
> 3. Na barra de pesquisa do topo, digite **"Senhas de app"**.
> 4. Digite o nome *"Live Monitor"* e clique em **Criar**.
> 5. Copie a senha amarela de 16 letras gerada e cole no campo `IMAP_PASSWORD` no arquivo `.env`. Pronto!

---

## 📱 Passo 3: Conectar o WhatsApp do Escritório (QR Code Único)

Você só precisa fazer isso **uma única vez**:

1. Dê um duplo clique no arquivo:  
   👉 **`scripts\conectar_whatsapp.bat`**
2. Uma janela do navegador vai se abrir na tela mostrando o **QR Code do WhatsApp Web**.
3. No celular do escritório:
   - Abra o WhatsApp.
   - Toque em **Configurações** (ou nos 3 pontinhos) $\rightarrow$ **Aparelhos Conectados** $\rightarrow$ **Conectar um Aparelho**.
   - Aponte a câmera para a tela do computador.
4. Assim que suas conversas carregarem, feche o navegador.
5. **Pronto!** O login ficou gravado em um cofre digital na pasta `data\whatsapp_session`. A partir de agora, o robô disparará as mensagens em segundo plano sem abrir nenhuma janela na tela.

---

## 🏢 Passo 4: Cadastrar as Empresas Clientes e seus Advogados

Abra o arquivo **`config\clients.yaml`** no Bloco de Notas. Você verá um modelo simples para preencher.

Para cada cliente que o seu escritório atende, basta preencher:
- **`name`**: Razão Social ou Nome Fantasia da empresa cliente.
- **`cnpj`**: O CNPJ da empresa.
- **`aliases`**: O e-mail ou apelido que foi configurado para ela (ex: `cliente_alfa@seuescritorio.com.br`).
- **`advogados`**: O nome e o WhatsApp do advogado do seu escritório responsável pelos processos dessa empresa.
- **`contadores`**: O nome e o WhatsApp do contador parceiro responsável pelo fiscal.

### Exemplo Prático de Preenchimento:
```yaml
clients:
  - id: "empresa-moveis-artisticos"
    name: "Móveis Artísticos Indústria e Comércio Ltda"
    cnpj: "12.345.678/0001-90"
    aliases:
      - "moveis@seuescritorio.com.br"
    destinatarios:
      advogados:
        - nome: "Dr. Marcelo (Jurídico Cível/Tributário)"
          whatsapp: "5561996993134"
          notificar_em: ["todos"]
      contadores:
        - nome: "Contabilidade São Jorge"
          whatsapp: "5561988887777"
          notificar_em: ["todos"]
```

> 💡 **Como funciona o Alias?**
> Peça para a empresa cliente cadastrar no portal da Receita Federal (e-CAC) ou nos órgãos o e-mail `moveis@seuescritorio.com.br`. Todos os avisos oficiais cairão na sua caixa central e o robô saberá na mesma hora que a mensagem pertence àquela empresa!

---

## ⚙️ Passo 5: Colocar o Robô em Operação

### Opção A: Execução Normal no Computador (Windows)
Basta dar um duplo clique no arquivo:  
👉 **`scripts\iniciar_monitoramento.bat`**

O robô ficará ativo e checará as caixas postais automaticamente 5 vezes ao dia:
- `08:30` (Abertura do expediente)
- `11:30` (Antes do almoço)
- `14:30` (Início da tarde)
- `17:30` (Fim de expediente dos órgãos públicos)
- `20:00` (Varredura noturna de fechamento)

### Opção B: Execução em Servidor ou Container Docker
Se o seu escritório utiliza servidor ou Docker, acesse a pasta `docker` e rode:
```bash
docker compose up -d
```
O serviço rodará silenciosamente no servidor 24 horas por dia, 7 dias por semana, reiniciando sozinho caso o servidor seja reiniciado.

---

## 🤖 Passo 6: O Agente Hermes Supervisionando Tudo

O **Hermes** é o assistente inteligente que gerencia o sistema para você. Você pode conversar com ele no seu **Telegram corporativo**:

- Se você mandar: *"Hermes, como estão as intimações hoje?"*
  - Ele responderá informando quantas foram checadas, quais órgãos enviaram notificações e para quem os alertas foram entregues.
- Se você mandar: *"Hermes, faça uma varredura agora!"*
  - Ele aciona o motor imediatamente, confere a caixa postal e avisa se há algum prazo novo.
- Se uma mensagem não puder ser entregue:
  - O Hermes te manda uma notificação de alerta imediatamente para você não perder nenhum prazo!

---

## 🛡️ Passo 7: Segurança, Sigilo OAB e LGPD

Para que seu escritório e seus clientes fiquem 100% resguardados perante a OAB e a LGPD:

1. **Inviolabilidade de Sigilo (OAB Art. 7º, II):** Cada empresa tem seus aliases e advogados estritamente segregados. Um advogado do cliente "A" nunca receberá notificações da empresa "B".
2. **Prova de Tempestividade:** Toda intimação recebe um código criptográfico SHA-256 e registro de data/hora, servindo como comprovante de que o escritório tomou ciência dentro do prazo.
3. **Minimização de Dados (LGPD):** Números de CPF e telefones são mascarados em relatórios públicos.
4. **Relatório de Auditoria:**
   Para gerar o laudo de conformidade para mostrar aos sócios ou clientes, basta dar um duplo clique em:  
   👉 **`scripts\auditoria_seguranca.bat`**

---

## ❓ Perguntas Frequentes (FAQ)

### 1. Se faltar energia ou a internet cair, eu perco as intimações?
**Não.** Os e-mails ficam guardados na sua caixa central da nuvem (Google ou Outlook). Assim que o computador ou servidor reconectar, o Live Monitor fará a leitura de todos os e-mails pendentes.

### 2. O mesmo e-mail pode ser enviado duas vezes no WhatsApp?
**Não.** O Live Monitor possui um banco de dados local com controle rigoroso de duplicidade (idempotência). Uma vez notificada, a mensagem nunca é repetida.

### 3. Preciso de autorização dos meus clientes?
**Não é necessário consentimento extra**, pois o tratamento dessas informações é respaldado pelo **Art. 7º, II da LGPD** (cumprimento de obrigação legal e regulatória de responder aos órgãos públicos tempestivamente).

### 4. Como altero os horários de checagem?
Abra o arquivo `.env` e altere a linha `SCHEDULE_TIMES`:
```env
SCHEDULE_TIMES=08:00,10:00,12:00,14:00,16:00,18:00
```
