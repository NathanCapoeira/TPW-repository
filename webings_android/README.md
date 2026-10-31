# The Path Of Webings — Android (Kivy)

Esta é uma migração da interface CustomTkinter para Kivy, mantendo o motor de jogo e a persistência SQLite.

## Testar no computador

```bash
python -m pip install kivy
python main.py
```

## Gerar APK (Linux ou WSL2 Ubuntu)

Instale os pré-requisitos do Buildozer e Android SDK/NDK conforme a documentação oficial do Kivy/Buildozer. Depois, dentro desta pasta:

```bash
python3 -m pip install buildozer
buildozer android debug
```

O APK compilado será gerado na pasta `bin/` após o build concluir. A primeira compilação baixa dependências e pode demorar.

**Importante:** esta entrega contém código-fonte e configuração de compilação; não é um APK já compilado. A interface precisa ser validada em um aparelho Android real. O arquivo `game_history.db` é gravado no diretório privado do aplicativo.
