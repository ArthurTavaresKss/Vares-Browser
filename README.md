# Vares Browser
## (VERSÃO DO README: 1.3.1 | VERSÃO ATUAL : 1.4.0)

**Status: Trabalho em Progresso (Fase Inicial com Interface Gráfica Avançada)**

O **Vares Browser** é um projeto educacional de navegador web em desenvolvimento, implementado em Python como parte do estudo do livro [*Web Browser Engineering*](https://browser.engineering/index.html) de Pavel Panchekha e Chris Harrelson. Este projeto, agora em uma fase inicial avançada, oferece uma interface gráfica funcional utilizando Tkinter, com suporte a renderização de texto, emojis, rolagem e redimensionamento de janela. O objetivo é criar um navegador simples, mas robusto, que eventualmente implementará funcionalidades como parsing de HTML, aplicação de CSS, execução de JavaScript e renderização completa, conforme descrito no livro.

## Funcionalidades Implementadas

O Vares Browser suporta as seguintes funcionalidades, correspondentes aos exercícios 1-1 a 1-9 do livro, com extensões para uma interface gráfica mais robusta e suporte a emojis:

- **Suporte a Protocolos**:
  - **HTTP/1.1**: Requisições com cabeçalhos `Host`, `Connection: keep-alive`, `User-Agent` e `Accept-Encoding: gzip`.
  - **HTTPS**: Conexões seguras com SSL/TLS, incluindo handshake SSL e validação de certificados.
  - **Esquema `file://`**: Carregamento de arquivos locais, com suporte a caminhos relativos e absolutos (ex.: `file:///caminho/para/arquivo.html`).
  - **Esquema `data:`**: Exibição de conteúdo inline (ex.: `data:text/html,Hello world!`), com suporte a codificação Base64.
  - **Esquema `view-source:`**: Exibição do código-fonte HTML de uma página, com caracteres `<` e `>` escapados adequadamente.
  - **Esquema `rlt:`**: Suporte a texto da direita para a esquerda, útil para idiomas como árabe e hebraico.

- **Gerenciamento de Conexões**:
  - **Keep-Alive**: Reutilização de sockets para múltiplas requisições ao mesmo servidor, com suporte a `Connection: keep-alive` e fechamento de conexão baseado em `Connection: close`.
  - **Redirecionamentos**: Suporte a códigos HTTP de redirecionamento (301, 302, 303, 307, 308), com resolução de URLs relativas e limite de 10 redirecionamentos para evitar loops.
  - **Cache**: Armazenamento em cache de respostas HTTP para códigos 200, 301 e 404, com suporte a `Cache-Control: no-store` e `max-age` para controle de expiração.

- **Processamento de Conteúdo**:
  - **Compressão**: Suporte a `Content-Encoding: gzip` e `Transfer-Encoding: chunked`, com descompressão automática de respostas gzip.
  - **Entidades HTML**: Renderização de entidades como `&lt;` e `&gt;` como `<` e `>`, respectivamente.
  - **Emojis**: Suporte a renderização de emojis via arquivos PNG armazenados na pasta `openmoji-72x72-color`, com dimensionamento automático (`EMOJI_SIZE = 18`).

- **Interface Gráfica**:
  - **Canvas Tkinter**: Janela gráfica de 800x600 pixels (redimensionável) para exibir texto e emojis extraídos de páginas web.
  - **Layout de Texto**: Posicionamento dinâmico de caracteres e emojis, com quebras de linha automáticas e suporte a quebras explícitas (`\n`).
  - **Rolagem**: Suporte a rolagem vertical usando teclas de seta (cima/baixo), roda do mouse (Windows e Linux) e controle de deslocamento (`SCROLL_STEP = 100` pixels).
  - **Barra de Rolagem**: Exibição de uma barra de rolagem dinâmica quando o conteúdo excede a altura da janela.
  - **Redimensionamento**: Ajuste automático do layout ao redimensionar a janela, recalculando posições com base na nova largura e altura.

- **Outras Funcionalidades**:
  - **Modo RTL (Right-to-Left)**: Suporte a texto da direita para a esquerda, com inversão de linhas para idiomas que requerem essa formatação.
  - **Arquivo Padrão**: Carregamento automático de `Default.html` quando nenhum URL é fornecido.
  - **Tratamento de Erros**: Gestão robusta de erros para conexões, timeouts, arquivos não encontrados e decodificação Base64.

**Nota**: O projeto está em uma fase inicial avançada, com foco em uma interface gráfica funcional. A renderização é limitada a texto puro e emojis, sem suporte a formatação HTML, CSS ou JavaScript.

## Pré-requisitos

- **Python**: Versão 3.6 ou superior.
- **Módulos Padrão**: `socket`, `ssl`, `sys`, `os`, `base64`, `time`, `gzip`, `tkinter`.
- **Dependências Externas**: Nenhuma, exceto a pasta `openmoji-72x72-color` para emojis (opcional, incluída no repositório).
- **Sistema Operacional**: Compatível com Windows, Linux e macOS (com ajustes para eventos de roda do mouse).

## Como Executar

1. **Clone o Repositório**:
   ```bash
   git clone https://github.com/ArthurTavaresKss/Vares-Browser.git
   cd Vares-Browser
   ```

2. **Execute o Navegador**:
   - Para carregar uma página web:
     ```bash
     python Browser.py https://example.org
     ```
   - Para exibir o código-fonte:
     ```bash
     python Browser.py view-source:https://example.org
     ```
   - Para carregar um arquivo local:
     ```bash
     python Browser.py file:///caminho/para/arquivo.html
     ```
   - Para testar o esquema `data:`:
     ```bash
     python Browser.py data:text/html,Hello%20world!
     ```
   - Para texto da direita para a esquerda:
     ```bash
     python Browser.py rlt:https://example.org
     ```
   - Sem argumentos, carrega `Default.html`:
     ```bash
     python Browser.py
     ```

3. **Interação**:
   - **Rolagem**: Use as teclas de seta (cima/baixo) ou a roda do mouse para navegar pelo conteúdo.
   - **Redimensionamento**: Arraste as bordas da janela para ajustar o tamanho; o conteúdo será reformatado automaticamente.
   - **Fechar**: Clique no botão de fechar da janela para encerrar o programa.

## Limitações Atuais

- **Renderização**: Apenas texto puro e emojis são exibidos, sem suporte a elementos HTML complexos, CSS ou JavaScript.
- **Fonte**: Usa a fonte padrão do Tkinter, sem opções de personalização de tamanho ou estilo.
- **Emojis**: Requer a pasta `openmoji-72x72-color` para renderização de emojis; caracteres sem PNG correspondente são exibidos como texto.
- **Funcionalidades Futuras**: Planejado para incluir parsing de HTML, aplicação de CSS, execução de JavaScript, suporte a formulários e renderização gráfica completa, conforme os capítulos futuros do livro.

## Contribuindo

O Vares Browser é um projeto educacional aberto a contribuições. Você pode ajudar com:

- Correção de bugs (ex.: cache, redirecionamentos, renderização de texto ou emojis).
- Implementação de funcionalidades dos próximos capítulos do livro, como parsing de HTML ou suporte a CSS.
- Melhorias na interface gráfica, como suporte a fontes personalizadas ou layouts mais complexos.

Para contribuir:
1. Fork o repositório.
2. Crie uma branch para sua feature ou correção (`git checkout -b feature/nova-funcionalidade`).
3. Envie um pull request com uma descrição clara das mudanças.

Por favor, abra issues no [GitHub](https://github.com/ArthurTavaresKss/Vares-Browser) para reportar bugs ou sugerir melhorias.

## Agradecimentos

Este projeto é baseado no livro [*Web Browser Engineering*](https://browser.engineering/index.html) de Pavel Panchekha e Chris Harrelson. Agradecemos aos autores por fornecerem um guia detalhado e acessível para a construção de um navegador web do zero. Também agradecemos à comunidade open-source, especialmente ao projeto OpenMoji, pela disponibilização dos arquivos de emojis utilizados.