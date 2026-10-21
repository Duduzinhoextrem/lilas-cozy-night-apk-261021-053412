# Lila's Cozy Night — APK Android (pacote de build experimental)

Este pacote contém os **arquivos reais enviados** do mod e scripts para produzir um APK Android do Codename Engine Mobile com o mod embutido. O APK NÃO está neste arquivo. A compilação e o teste no celular ainda não foram realizados.

**Fonte do port:** https://github.com/CPsP-Team/CodenameEngine-Mobile

**Revisão travada:** `4af5529d60ebf2599372cd95463acfd6707c5cdd` — release `mobile-legacy` (1.0.1).

**O que muda:**
- APK com nome `Lila's Cozy Night` e `packageName=com.dudz.lilas.cozy.night` (não substitui o Codename original)
- Ícone derivado de um asset fornecido no mod
- Inclui todas as músicas, scripts e sprites do ZIP original sem mudar o conteúdo
- Fonte Android é configurada para selecionar `lilas-cozy-night` automaticamente
- Ao abrir o APK, tenta copiar os mods de seus assets instalados para a pasta privada do próprio aplicativo
- Não precisa usar ZArchiver para copiar mods para Android/data

## Gerar APK usando GitHub Actions

1. Crie um repositório **privado** vazio no GitHub (o mod contém músicas e arquivos para uso pessoal).
2. Descompacte este pacote numa pasta **no computador**. O arquivo do mod tem cerca de 77 MB, acima do limite de upload pela interface web do GitHub; envie pelo Git no terminal (exemplo abaixo). Inclua a pasta oculta `.github/workflows/`.
3. Em GitHub -> Actions -> `Gerar APK Lila Cozy Night` -> Run workflow.
4. Ao finalizar, baixe o artifact `Lila-Cozy-Night-APK-ARM64` da execução e extraia o arquivo `.apk`.
5. Instale o APK no celular Android ARM64. Para instalação fora da loja, o Android pede autorização de 'Instalar apps desconhecidos' para o aplicativo pelo qual você abrir o APK.

No terminal, dentro da pasta extraída, substitua `SEU_USUARIO` e `SEU_REPOSITORIO` por seus dados:

```sh
git init -b main
git add .
git commit -m "Preparar build Android da Lila"
git remote add origin https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
git push -u origin main
```

> Se o GitHub não encontrar um workflow, confira se a pasta `.github` foi enviada. Se Actions for bloqueado no repositório, habilite-os em Settings -> Actions.

## Compilação local (para quem já tem Haxe/Android SDK)

1. Instale Haxe 4.3.7, Android SDK, Android NDK r25c e JDK 17.
2. Clone a revisão exata do engine:

```sh
git clone https://github.com/CPsP-Team/CodenameEngine-Mobile.git engine
cd engine
git checkout 4af5529d60ebf2599372cd95463acfd6707c5cdd
cd ..
python3 scripts/prepare_engine.py --engine engine
cd engine
haxe -cp commandline -D analyzer-optimize --run Main setup -s
haxelib run lime setup -alias -y
haxelib run lime config ANDROID_SDK "$ANDROID_HOME"
haxelib run lime config ANDROID_NDK_ROOT "$ANDROID_NDK_HOME"
haxelib run lime config JAVA_HOME "$JAVA_HOME"
haxelib run lime config ANDROID_SETUP true
haxelib run lime build android -final -D ONLY_ARM64
```

A compilação Android pode necessitar de ajustes de dependências e dos caminhos SDK/NDK no computador.

## Diagnóstico dos primeiros testes

- O app instala mas só mostra o menu da engine: procurar `COZY_APK source missing` ou `COZY_APK copy failed` no logcat. O port pode não extrair `mods/` automaticamente, exigindo alterar o método de extração da versão usada.
- Travamentos nos menus/cutscenes: scripts e assets não foram testados nesta build; verificar logcat primeiro.
- Instalou mas não carrega um pacote após atualização: apagar os dados **apenas deste novo APK** reinicia a importação (apaga saves deste APK).
- Tamanho ou performance: personagem com atlases grandes; usar um APK ARM64 reduz binários para dispositivos atuais, mas não resolve consumo de memória dos sprites.

**Limites:** Não foi possível compilar nesta sessão (sem Haxe, Android SDK/NDK e sem acesso externo para baixar dependências). Este é um **projeto de compilação experimental**, não um APK garantido ou um jogo testado.

Créditos da engine e do port permanecem com seus autores; veja CREDITS.md.
