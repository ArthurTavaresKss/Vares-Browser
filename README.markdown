# Vares Browser

**Status: Trabalho em Progresso (Fase Inicial)**

O **Vares Browser** é um projeto de navegador web em desenvolvimento, construído em Python como parte do estudo do livro [*Web Browser Engineering*](https://browser.engineering/index.html) de Pavel Panchekha e Chris Harrelson. Este projeto é um trabalho em progresso, atualmente focado na implementação de funcionalidades básicas de rede para carregar páginas web, sem suporte a interface gráfica (GUI) ou renderização visual de páginas. O objetivo é criar um navegador simples, mas funcional, que eventualmente cobrirá aspectos como parsing de HTML, aplicação de CSS, execução de JavaScript e mais, conforme descrito no livro.

## Funcionalidades Implementadas

Atualmente, o Vares Browser suporta as seguintes funcionalidades, correspondentes aos exercícios 1-1 a 1-9 do livro:

- **HTTP/1.1 (Exercício 1-1)**: Suporte a requisições HTTP/1.1 com cabeçalhos `Host`, `Connection: keep-alive`, e `User-Agent`.
- **URLs de Arquivo (Exercício 1-2)**: Suporte ao esquema `file://` para abrir arquivos locais, com um arquivo padrão (`Default.html`) carregado quando nenhum URL é fornecido.
- **Esquema Data (Exercício 1-3)**: Suporte ao esquema `data:` para exibir conteúdo HTML inline (ex.: `data:text/html,Hello world!`).
- **Entidades HTML (Exercício 1-4)**: Renderização de entidades `&lt;` e `&gt;` como `<` e `>`, respectivamente.
- **View-Source (Exercício 1-5)**: Suporte ao esquema `view-source:` para exibir o código-fonte HTML de uma página.
- **Keep-Alive (Exercício 1-6)**: Reutilização de sockets para requisições ao mesmo servidor, usando `Connection: keep-alive` e leitura baseada em `Content-Length`.
- **Redirecionamentos (Exercício 1-7)**: Suporte a redirecionamentos HTTP (códigos 301, 302, 303, 307, 308) com resolução de URLs relativas e limite de 10 redirecionamentos.
- **Cache (Exercício 1-8)**: Cache de respostas HTTP para códigos 200, 301 e 404, com suporte parcial a `Cache-Control: no-store` e `max-age`.
- **Compressão (Exercício 1-9)**: Suporte a compressão HTTP com `Accept-Encoding: gzip`, descompressão de respostas com `Content-Encoding: gzip`, e suporte a `Transfer-Encoding: chunked`.

**Nota**: O projeto está em sua fase inicial, focado apenas na parte de carregamento de páginas (Part 1 do livro). Não há suporte a renderização visual, parsing de HTML, CSS, JavaScript ou interface gráfica. Algumas funcionalidades, como a resolução de URLs relativas em redirecionamentos e a lógica de cache, precisam de melhorias para total conformidade com os exercícios.

## Como Executar

### Pré-requisitos
- Python 3.6 ou superior
- Módulos padrão: `socket`, `ssl`, `sys`, `os`, `base64`, `time`, `gzip`

### Instruções
1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/vares-browser.git
   cd vares-browser
   ```
2. Crie um arquivo `Default.html` no mesmo diretório para testes locais (opcional).
3. Execute o navegador com um URL:
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
4. Se nenhum URL for fornecido, o navegador tentará carregar `Default.html` do diretório atual.

### Exemplos de Uso
- Carregar uma página web:
  ```bash
  python Browser.py https://example.org
  ```
  **Saída**: Exibe o texto visível da página (sem tags HTML).
- Carregar um arquivo local:
  ```bash
  python Browser.py file:///D:/Codes/Python/WebBrowser/Default.html
  ```
- Testar o esquema `data`:
  ```bash
  python Browser.py data:text/html,Hello%20world!
  ```
  **Saída**: `Hello world!`

## Limitações Atuais
- **Sem Interface Gráfica**: O navegador apenas exibe o texto visível das páginas no console, sem renderização visual.
- **Cache Imperfeito**: O cache armazena respostas com bytes em vez de strings decodificadas e não ignora corretamente valores de `Cache-Control` além de `no-store` e `max-age`.
- **Redirecionamentos**: A resolução de URLs relativas complexas (ex.: `../page`) pode falhar.
- **Funcionalidades Futuras**: Planejado para incluir parsing de HTML, layout, CSS, JavaScript e renderização gráfica, conforme os capítulos futuros do livro.

## Contribuindo
Este é um projeto educacional em andamento. Contribuições são bem-vindas, especialmente para corrigir bugs (ex.: cache e redirecionamentos) ou implementar os próximos capítulos do livro. Por favor, abra issues ou pull requests no [GitHub](https://github.com/seu-usuario/vares-browser).

## Licença
Este projeto é licenciado sob a [MIT License](LICENSE).

## Agradecimentos
Este projeto segue o livro [*Web Browser Engineering*](https://browser.engineering/index.html) de Pavel Panchekha e Chris Harrelson. Agradecimentos aos autores por fornecerem um guia detalhado para construir um navegador web do zero.