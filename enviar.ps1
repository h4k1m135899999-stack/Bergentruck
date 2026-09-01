param(
    [string]$mensagem = "atualização"
)

Set-Location 'c:\Users\DELL\Documents\Bergentruck 2\The_last_Bergentruck'

git add .
git commit -m $mensagem
git push
