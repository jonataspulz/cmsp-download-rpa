# RPA - Centro de Mídias SP

🇧🇷 [Português (Brasil)](#português-brasil) · 🇺🇸 [English](#english)

---

## Português (Brasil)

Script em **Python + Selenium** que baixa automaticamente os **materiais digitais** (PDF, PPT e PPTX) do repositório de mídias do CMSP (Centro de Mídias SP), da Secretaria da Educação do Estado de São Paulo. Em vez de clicar em cada botão de download, você configura o que quer e deixa o programa trabalhar.

> **Aviso:** projeto independente, sem vínculo com a Secretaria da Educação do Estado de São Paulo nem com o CMSP. Use apenas com a sua própria conta e respeitando os termos de uso do site e os direitos autorais dos materiais.

### O que o programa faz

- Percorre **Ano letivo → Etapa → Série/Ano → Semestre/Bimestre → Componente Curricular**, preenchendo os filtros da página sozinho.
- **Descobre os componentes curriculares** disponíveis para cada combinação de ano, etapa, série e bimestre (ignorando "SELECIONE") e usa todos eles. Se preferir, você pode limitar a alguns.
- Baixa **todos os materiais** da lista: aulas, livros do estudante, cadernos, jornadas de revisão etc., em PDF/PPT/PPTX, **inclusive os da aba "Acessibilidade Curricular"**.
- Organiza tudo em pastas e **não baixa de novo** o que já existe.

### Requisitos

- Windows 10/11 (pensado para Windows; em macOS/Linux deve funcionar ajustando os comandos do Chrome, mas não foi testado).
- **Google Chrome** instalado.
- **Python 3.13 ou mais novo**.
- Uma conta com acesso ao site (o login é feito por você, manualmente, no Chrome, com a conta gov.br).


## English

**Python + Selenium** script that automatically downloads the **digital materials** (PDF, PPT and PPTX) from the CMSP (Centro de Mídias SP) media repository of the São Paulo State Department of Education. Instead of clicking every download button, you set what you want and let the program work.

> **Disclaimer:** independent project, not affiliated with the São Paulo State Department of Education or with CMSP. Use it only with your own account, and respect the site's terms of use and the copyright of the materials.

### What the program does

- Goes through **School year → Stage → Grade → Semester/Term → Subject** ("Componente Curricular"), filling in the page filters by itself.
- **Discovers the subjects** available for each combination of year, stage, grade and term (ignoring "SELECIONE") and uses all of them. You can restrict it to some subjects if you prefer.
- Downloads **every material** in the list: lessons, student books, workbooks, review journeys, etc., as PDF/PPT/PPTX, **including the ones in the "Acessibilidade Curricular" tab**.
- Organizes everything into folders and **does not download again** what already exists.

### Requirements

- Windows 10/11 (built for Windows; on macOS/Linux it should work after adjusting the Chrome commands, but this was not tested).
- **Google Chrome** installed.
- **Python 3.10 or newer** (the code uses `match`).
- An account with access to the site (you log in yourself, manually, in Chrome, using gov.br).


#### 🇺🇸 Full MIT License Text

text

MIT License

Copyright (c) 2026 Jonatas Pulz

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Use code with caution.

#### 🇧🇷 Texto Completo da Licença MIT

text

Licença MIT

Copyright (c) 2026 Jonatas Pulz

É concedida permissão, gratuitamente, a qualquer pessoa que obtenha uma cópia
deste software e dos arquivos de documentação associados (o "Software"), para
lidar com o Software sem restrições, incluindo, sem limitação, os direitos de
usar, copiar, modificar, mesclar, publicar, distribuir, sublicenciar e/ou vender
cópias do Software, e permitir que as pessoas a quem o Software é fornecido o
façam, mediante as seguintes condições:

O aviso de copyright acima e este aviso de permissão devem ser incluídos em todas
as cópias ou partes substanciais do Software.

O SOFTWARE É FORNECIDO "COMO ESTÁ", SEM GARANTIA DE QUALQUER TIPO, EXPRESSA OU
IMPLÍCITA, INCLUINDO, MAS NÃO SE LIMITANDO ÀS GARANTIAS DE COMERCIALIZAÇÃO,
ADEQUAÇÃO A UM DETERMINADO FIM E NÃO INFRAÇÃO. EM NENHUM CASO OS AUTORES OU
TITULARES DE DIREITOS AUTORAIS SERÃO RESPONSÁVEIS POR QUALQUER REIVINDICAÇÃO,
DANOS OU OUTRA RESPONSABILIDADE, SEJA EM AÇÃO DE CONTRATO, ILÍCITO OU DE OUTRA
FORMA, DECORRENTE DE, FORA OU EM CONEXÃO COM O SOFTWARE OU O USO OU OUTRAS
NEGOCIAÇÕES NO SOFTWARE.

Use code with caution.