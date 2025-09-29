# Vares Browser

**Status: Trabalho em Progresso (Fase Inicial com Interface Gráfica)**

O **Vares Browser** é um projeto de navegador web em desenvolvimento, construído em Python como parte do estudo do livro [*Web Browser Engineering*](https://browser.engineering/index.html) de Pavel Panchekha e Chris Harrelson. Este projeto é um trabalho em progresso, agora com uma interface gráfica básica usando Tkinter, focada em carregar e exibir texto de páginas web com suporte a rolagem. O objetivo é criar um navegador simples, mas funcional, que eventualmente cobrirá aspectos como parsing de HTML, aplicação de CSS, execução de JavaScript e mais, conforme descrito no livro.

## Funcionalidades Implementadas

Atualmente, o Vares Browser suporta as seguintes funcionalidades, correspondentes aos exercícios 1-1 a 1-9 do livro, com adições para interface gráfica:

- **HTTP/1.1**: Suporte a requisições HTTP/1.1 com cabeçalhos `Host`, `Connection: keep-alive`, e `User-Agent`.
- **URLs de Arquivo**: Suporte ao esquema `file://` para abrir arquivos locais, com um arquivo padrão (`Default.html`) carregado quando nenhum URL é fornecido.
- **Esquema Data**: Suporte ao esquema `data:` para exibir conteúdo HTML inline (ex.: `data:text/html,Hello world!`).
- **Entidades HTML**: Renderização de entidades `&lt;` e `&gt;` como `<` e `>`, respectivamente.
- **View-Source**: Suporte ao esquema `view-source:` para exibir o código-fonte HTML de uma página.
- **Keep-Alive**: Reutilização de sockets para requisições ao mesmo servidor, usando `Connection: keep-alive` e leitura baseada em `Content-Length`.
- **Redirecionamentos**: Suporte a redirecionamentos HTTP (códigos 301, 302, 303, 307, 308) com resolução de URLs relativas e limite de 10 redirecionamentos.
- **Cache**: Cache de respostas HTTP para códigos 200, 301 e 404, com suporte parcial a `Cache-Control: no-store` e `max-age`.
- **Compressão**: Suporte a compressão HTTP com `Accept-Encoding: gzip`, descompressão de respostas com `Content-Encoding: gzip`, e suporte a `Transfer-Encoding: chunked`.
- **Interface Gráfica**: Interface básica usando Tkinter com um canvas de 800x600 pixels para exibir texto extraído de páginas web.
- **Layout de Texto**: Função `layout` que posiciona caracteres no canvas, com suporte a quebras de linha automáticas e quebras explícitas (`\n`).
- **Rolagem (Scrolling)**: Suporte a rolagem vertical usando as teclas de seta (cima/baixo), roda do mouse (Windows e Linux) e controle de deslocamento (`SCROLL_STEP = 100` pixels).

**Nota**: O projeto está em sua fase inicial, com uma interface gráfica básica. A renderização é limitada a texto puro, sem suporte a formatação HTML, CSS ou JavaScript.

## Como Executar

### Pré-requisitos
- Python 3.6 ou superior
- Módulos padrão: `socket`, `ssl`, `sys`, `os`, `base64`, `time`, `gzip`, `tkinter`

### Instruções
1. Clone o repositório:
   ```bash
   git clone https://github.com/ArthurTavaresKss/Vares-Browser.git
   cd Vares-Browser
   ```
2. Execute o navegador com um URL:
   ```bash
   python Browser.py https://example.org
   ```
   ou para um arquivo local:
   ```bash
   python Browser.py file:///caminho/para/arquivo.html
   ```
   ou para exibir código-fonte:
   ```bash
   python Browser.py view-source:https://example.org
   ```
3. Se nenhum URL for fornecido, o navegador tentará carregar `Default.html` do diretório padrão do Browser.

### Exemplos de Uso
- Carregar uma página web:
  ```bash
  python Browser.py https://example.org
  ```
  **Saída**: Exibe o texto visível da página em uma janela gráfica com suporte a rolagem.
- Carregar o código-fonte de uma página web:
  ```bash
  python Browser.py view-source:https://example.org
  ```
  **Saída**: Exibe o código-fonte HTML na janela gráfica.
- Carregar um arquivo local:
  ```bash
  python Browser.py file:///D:/Codes/Python/WebBrowser/Default.html
  ```
  **Saída**: Exibe o texto do arquivo na janela gráfica.
- Testar o esquema `data`:
  ```bash
  python Browser.py data:text/html,Hello world!
  ```
  **Saída**: Exibe `Hello world!` na janela gráfica.

### Interação
- **Rolagem**: Use as teclas de seta (cima/baixo) ou a roda do mouse para rolar o conteúdo verticalmente.
- **Fechar**: Feche a janela gráfica para encerrar o programa.

## Limitações Atuais
- **Renderização Limitada**: A interface gráfica exibe apenas texto puro, sem formatação (ex.: negrito, itálico) ou suporte a elementos HTML complexos.
- **Fonte Padrão**: O texto é desenhado com a fonte padrão do Tkinter, sem configuração de tamanho ou estilo.
- **Sem CSS/JavaScript**: Não há suporte a parsing de HTML, aplicação de CSS ou execução de JavaScript.
- **Funcionalidades Futuras**: Planejado para incluir parsing de HTML, layout mais avançado, suporte a CSS, JavaScript e renderização completa, conforme os capítulos futuros do livro.

## Contribuindo
Este é um projeto educacional em andamento. Contribuições são bem-vindas, especialmente para corrigir bugs (ex.: cache, redirecionamentos, ou renderização de texto) ou implementar os próximos capítulos do livro. Por favor, abra issues ou pull requests no [GitHub](https://github.com/ArthurTavaresKss/Vares-Browser).

## Agradecimentos
Este projeto segue o livro [*Web Browser Engineering*](https://browser.engineering/index.html) de Pavel Panchekha e Chris Harrelson. Agradecimentos aos autores por fornecerem um guia detalhado para ajudar na construção de um navegador web do zero.