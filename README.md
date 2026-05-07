# prompt-auto-log

Ferramenta de logging automático de prompts de IA generativa no VSCode. A cada mensagem enviada ao Claude, Codex ou Copilot, o hook captura o texto do prompt e salva em arquivos JSON locais **por usuário**.

Também pode servir como base para fluxos de outras IAs no editor, adaptando os eventos/hooks conforme a ferramenta utilizada.

## Pré-requisitos:

- Bash
- `jq`
- Git com `user.name` e `user.email` configurados

## Como funciona

Os agentes de IA permitem configurar **hooks**: scripts que são executados automaticamente em resposta a eventos. Este projeto usa o evento `UserPromptSubmit`, disparado toda vez que o usuário envia uma mensagem.

Quando um prompt é enviado:

1. O agente executa o script `.ai_log/log_prompts.sh`
2. O script recebe o conteúdo do prompt via `stdin` (em formato JSON)
3. Tags de contexto da IDE (como `<ide_opened_file>` e `<ide_selection>`) são removidas automaticamente, salvando apenas o texto digitado pelo usuário
4. A entrada é salva em `.ai_log/prompt_log_YYYY-MM-DD_usuario.json`, com timestamp, branch, usuário git e origem do agente (`claude` ou `codex`)

## Configuração dos hooks

Este repositório já inclui exemplos de configuração para os dois agentes:

- Claude: [.claude/settings.json](.claude/settings.json)
- Codex e Copilot: [.github/hooks/hooks.json](.github/hooks/hooks.json)

Ambos chamam o mesmo script de logging e definem a origem via variável de ambiente `PROMPT_LOG_SOURCE`.

## Como usar no seu projeto

Rode os comandos a seguir dentro do seu repositório:

```bash
git remote add prompt-auto-log https://github.com/pucrs-disciplinas/prompt-auto-log.git
git fetch prompt-auto-log
git merge --allow-unrelated-histories prompt-auto-log/main -m "merge: integra prompt-auto-log"
git remote remove prompt-auto-log
git status
git push
```

Depois disso, toda interação com os agentes será registrada em arquivos dentro de `.ai_log/`.
