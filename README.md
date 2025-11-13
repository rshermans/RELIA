README.md Atualizado para https://github.com/rshermans/RELIA
markdown
# RELIA - Roteiro Empático de Leitura com Inteligência Artificial

RELIA é uma aplicação web inovadora que combina Processamento de Linguagem Natural (PLN), teoria literária e pedagogia para criar percursos de leitura personalizados e empáticos. A ferramenta utiliza inteligência artificial generativa para analisar textos literários e gerar experiências de leitura guiada adaptadas a leitores individuais.

## 🚀 Funcionalidades Principais

- **Análise de Texto Literário**: Processamento automático de obras literárias usando técnicas avançadas de PLN
- **Geração de Percursos de Leitura**: Criação de roteiros empáticos personalizados com base no perfil do leitor
- **Interface Web Intuitiva**: Aplicação acessível via navegador usando Streamlit
- **Arquitetura Aberta e Modular**: Código-fonte disponível para customização e extensão
- **Integração com APIs de IA**: Utilização de modelos generativos para análise textual

## 🛠️ Instalação e Configuração

Para executar o RELIA localmente:

1. **Clone o repositório**:
```bash
git clone https://github.com/rshermans/RELIA.git
cd RELIA
Instale as dependências:

bash
pip install -r requirements.txt
Configure as variáveis de ambiente:

bash
# Configure suas chaves de API para serviços de IA
export OPENAI_API_KEY="sua_chave_aqui"
Execute a aplicação:

bash
streamlit run app.py
📁 Estrutura do Projeto
text
RELIA/
├── app.py                      # Aplicação principal Streamlit
├── requirements.txt            # Dependências do projeto
├── README.md                   # Documentação
├── src/                       # Código-fonte
│   ├── text_processor.py      # Processamento de texto e NLP
│   ├── ai_integration.py      # Integração com APIs de IA
│   └── pedagogical_engine.py  # Módulo pedagógico e literário
├── data/                      # Dados e recursos
│   └── sample_texts/          # Textos literários de exemplo
└── tests/                     # Testes unitários
🎯 Como Usar
Acesso via Web: A aplicação está disponível em [Link para Streamlit Cloud] (em implantação)

Input de Texto: Insira ou faça upload de textos literários

Configuração do Perfil: Defina objetivos de leitura e preferências

Geração de Roteiro: O RELIA criará automaticamente um percurso de leitura empático

Exportação: Salve ou compartilhe os resultados para uso educacional

🔧 Tecnologias Utilizadas
Python 3.8+

Streamlit - Framework para aplicações web

OpenAI API - Modelos de linguagem generativa

NLTK/Spacy - Processamento de linguagem natural

Pandas - Manipulação de dados

Plotly - Visualizações interativas

🤝 Contribuições
Contribuições são bem-vindas! Se você é pesquisador, educador ou desenvolvedor interessado em Humanidades Digitais:

Faça um fork do projeto

Crie uma branch para sua feature (git checkout -b feature/AmazingFeature)

Commit suas mudanças (git commit -m 'Add some AmazingFeature')

Push para a branch (git push origin feature/AmazingFeature)

Abra um Pull Request

📄 Licença
Este projeto está licenci sob a Licença MIT - veja o arquivo LICENSE para detalhes.

📚 Publicação Científica
Se usar o RELIA em sua pesquisa ou ensino, por favor cite:
http://dx.doi.org/10.1007/978-3-032-05673-3_6
bibtex
@inproceedings{sherman2025relia,
  title={RELIA: Empathetic Reading Guide with Generative Artificial Intelligence},
  author={Sherman, Rômulo and Araújo, Sílvia},
  booktitle={IFIP Advances in Information and Communication Technology},
  volume={770},
  year={2025},
  publisher={Springer}
}
📞 Contato
Rômulo Sherman Magalhães

Doutorando em Ciências da Linguagem - Universidade do Minho

Email: [rsherman@ualumni.uminho.pt]

LinkedIn: linkedin.com/in/romulosherman

Projeto RELIA: https://github.com/rshermans/RELIA

🔗 Links Relacionados
Artigo Científico - Springer Link
https://hdl.handle.net/1822/96442
Repositório da Tese - Universidade do Minho

Aliança Arqus - Open Science Award

Desenvolvido no âmbito do doutoramento em Ciências da Linguagem, Universidade do Minho, com financiamento FCT (2024.07537.IACDC)

text

---

### **Arquivo LICENSE (MIT License)**

```text
MIT License

Copyright (c) 2025 Rômulo Sherman Magalhães

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
