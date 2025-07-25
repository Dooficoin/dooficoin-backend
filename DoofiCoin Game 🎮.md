# DoofiCoin Game 🎮

Um jogo de mineração e batalha em tempo real desenvolvido com React e Flask.

## 🚀 Funcionalidades

### ✅ Sistema Completo Implementado:
- **Autenticação**: Login e registro de usuários
- **Arena de Batalha**: Mate monstros, auto-eliminação e PvP
- **Sistema de Mineração**: Mine DoofiCoin automaticamente
- **Cenários Mundiais**: Explore locais famosos ao redor do mundo
- **Sistema de Níveis**: Progressão baseada em kills (90 jogadores ou 500 monstros)
- **Inventário e Loja**: Compre e gerencie itens raros
- **Cartas Colecionáveis**: Colecione cartas temáticas por país/cenário
- **Sistema de Ranking**: Leaderboards globais
- **Painel Administrativo**: Gerenciamento completo do jogo
- **Sistema de Anúncios**: Integração com Google AdSense
- **Segurança**: Logs de segurança e proteção contra fraudes

### 🎯 Características Especiais:
- **Itens Raros**: Sistema de raridade com cores (comum, raro, épico, lendário, mítico)
- **Variedade de Monstros**: 5 tipos diferentes (Zumbis, Animais, Robôs, Mutantes, Elementais)
- **Cenários Realistas**: 15 cenários únicos em 5 países com coordenadas geográficas reais
- **Progressão Ilimitada**: Fases infinitas com dificuldade crescente
- **Design Responsivo**: Interface moderna compatível com desktop e mobile

## 🛠️ Tecnologias Utilizadas

### Frontend:
- **React 18** com Vite
- **Tailwind CSS** para estilização
- **shadcn/ui** para componentes
- **Lucide React** para ícones
- **Recharts** para gráficos

### Backend:
- **Flask** com SQLAlchemy
- **SQLite** para banco de dados
- **JWT** para autenticação
- **bcrypt** para hash de senhas
- **CORS** habilitado

## 📦 Estrutura do Projeto

```
dooficoin-game/
├── src/
│   ├── models/          # Modelos do banco de dados
│   ├── routes/          # Rotas da API
│   ├── utils/           # Utilitários e helpers
│   ├── database.py      # Configuração do banco
│   └── main.py          # Aplicação principal
├── requirements.txt     # Dependências Python
└── vercel.json         # Configuração Vercel

dooficoin-frontend/
├── src/
│   ├── components/      # Componentes React
│   ├── App.jsx         # Componente principal
│   └── main.jsx        # Ponto de entrada
├── package.json        # Dependências Node.js
├── vite.config.js      # Configuração Vite
└── vercel.json         # Configuração Vercel
```

## 🚀 Implantação

### 1. Backend no Vercel

1. Faça upload do diretório `dooficoin-game` para um repositório GitHub
2. Conecte o repositório ao Vercel
3. Configure as variáveis de ambiente:
   ```
   FLASK_ENV=production
   SECRET_KEY=sua_chave_secreta_aqui
   ```
4. O Vercel detectará automaticamente o Flask e fará o deploy

### 2. Frontend no Vercel

1. Faça upload do diretório `dooficoin-frontend` para um repositório GitHub
2. Conecte o repositório ao Vercel
3. Configure o comando de build: `npm run build`
4. Configure o diretório de output: `dist`
5. Atualize a URL da API no arquivo `vercel.json` com a URL do backend

### 3. Configuração Local para Desenvolvimento

#### Backend:
```bash
cd dooficoin-game
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
pip install -r requirements.txt
cd src
python main.py
```

#### Frontend:
```bash
cd dooficoin-frontend
npm install
npm run dev
```

## 🎮 Como Jogar

1. **Registro**: Crie uma conta com username e email
2. **Arena**: Comece matando monstros para ganhar XP e DoofiCoin
3. **Mineração**: Inicie a mineração automática para ganhar moedas passivamente
4. **Progressão**: Mate 90 jogadores ou 500 monstros para subir de nível
5. **Exploração**: Desbloqueie novos cenários conforme avança
6. **Coleção**: Colete cartas e itens raros únicos de cada fase
7. **Competição**: Suba no ranking global

## 🔧 Configurações Administrativas

Acesse o painel administrativo para:
- Gerenciar usuários e jogadores
- Criar/editar itens e suas propriedades
- Configurar cenários e monstros
- Gerenciar cartas colecionáveis
- Configurar Google AdSense
- Visualizar logs de segurança
- Ajustar configurações do jogo

## 📊 Sistema de Economia

- **DoofiCoin**: Moeda principal do jogo
- **Mineração**: Inicia com 0,00000000000000000000000000000000001 DOOF
- **Progressão**: Tempo de mineração dobra a cada marco atingido
- **Recompensas**: Monstros e PvP dão diferentes quantidades de moedas
- **Loja**: Compre itens com DoofiCoin para melhorar seu personagem

## 🛡️ Segurança

- Autenticação JWT
- Proteção contra fraudes
- Logs de segurança detalhados
- Validação de entrada em todas as rotas
- Rate limiting para APIs críticas

## 📱 Compatibilidade

- ✅ Desktop (Chrome, Firefox, Safari, Edge)
- ✅ Mobile (iOS Safari, Android Chrome)
- ✅ Tablet (iPad, Android tablets)

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 🎯 Status do Projeto

✅ **PRONTO PARA PRODUÇÃO**

O jogo está completamente funcional e testado, pronto para ser implantado no GitHub e Vercel.

---

**Desenvolvido com ❤️ para a comunidade de jogos**

