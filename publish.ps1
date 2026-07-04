# Publishes this folder as a public GitHub repo + release.
# PREREQUISITE (you must do this once, it opens a browser):  gh auth login
#
# Then just run:  powershell -ExecutionPolicy Bypass -File publish.ps1
param(
  [string]$Repo = "vc2-korean-patch",
  [string]$Desc = "Valkyria Chronicles 2 (PSP) Korean fan-translation patch — xdelta, requires your own NPJH50145 ISO"
)

# locate gh
$gh = (Get-Command gh -ErrorAction SilentlyContinue).Source
if (-not $gh) { $gh = (Get-ChildItem "$env:LOCALAPPDATA\Microsoft\WinGet" -Recurse -Filter gh.exe -ErrorAction SilentlyContinue | Select-Object -First 1).FullName }
if (-not $gh) { Write-Error "gh CLI not found."; exit 1 }

# check auth
& $gh auth status 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Host "You are not logged in. Run:  gh auth login   (choose GitHub.com, HTTPS, login with browser)" -ForegroundColor Yellow
  exit 1
}

Set-Location $PSScriptRoot

# create repo (public) from current folder and push
& $gh repo create $Repo --public --source=. --remote=origin --push --description $Desc
if ($LASTEXITCODE -ne 0) { Write-Error "repo create failed"; exit 1 }

# create the release with the patch attached
$notes = @"
**전장의 발큐리아 2 (PSP, NPJH50145) 한글패치 v19**

원본 ISO(NPJH50145 v1.01)를 가진 분만 적용할 수 있는 xdelta 패치입니다. 적용 방법·번역 범위·제한 사항은 README를 참고하세요.

- 스토리 대사 전체 + 미션 브리핑/전투 대사(191) + UI/메뉴/튜토리얼 한글화
- 적용: Delta Patcher(GUI) 또는 ``python apply_patch.py 원본.iso``
- 결과 ISO SHA1: b355f638e7842aa861b90aafa8fcc6f6ff96564d
"@
& $gh release create v19 VC2_KoreanPatch_v19.xdelta --title "VC2 한글패치 v19" --notes $notes
if ($LASTEXITCODE -ne 0) { Write-Error "release create failed"; exit 1 }

$user = (& $gh api user --jq .login)
Write-Host "`nDONE → https://github.com/$user/$Repo/releases/tag/v19" -ForegroundColor Green
