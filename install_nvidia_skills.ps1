$ErrorActionPreference = "Continue"
$skillsDir = "C:\Users\ADMIN\.DEMON\skill-cache\github\skills\skills"
$skills = Get-ChildItem $skillsDir -Directory | Select-Object -ExpandProperty Name
$total = $skills.Count
$installed = 0; $skipped = 0; $failed = 0; $i = 0

Write-Host "Installing $total NVIDIA skills into DEMON..." -ForegroundColor Cyan

foreach ($skill in $skills) {
    $i++
    Write-Host "[$i/$total] $skill" -NoNewline
    $out = & uv run DEMON skill install "github:$skill" --url https://github.com/NVIDIA/skills 2>&1 | Out-String
    if ($out -match "Installed:") {
        Write-Host " OK" -ForegroundColor Green
        $installed++
    } elseif ($out -match "already installed") {
        Write-Host " already" -ForegroundColor DarkGray
        $skipped++
    } else {
        Write-Host " FAILED" -ForegroundColor Red
        $failed++
    }
}

Write-Host ""
Write-Host "===== NVIDIA Skills Install Complete =====" -ForegroundColor Cyan
Write-Host "Installed : $installed" -ForegroundColor Green
Write-Host "Skipped   : $skipped"
Write-Host "Failed    : $failed" -ForegroundColor Red
Write-Host "Total     : $total"
