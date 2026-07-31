$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$htmlPath = Join-Path $root 'ai-learning-roadmap.html'
$assetPath = Join-Path $root 'assets/animal-island/animal-icon.png'
$html = Get-Content -Raw -Encoding UTF8 -LiteralPath $htmlPath

$required = @(
    'id="animal-island-theme"',
    '--island-primary: #19c8b9',
    '--island-paper: #fff8e8',
    'class="header-mascot"',
    'assets/animal-island/animal-icon.png',
    "const STORAGE_KEY = 'ai_roadmap_progress_v2'",
    'function renderAll()',
    'function toggleDayPanel(h)',
    'onclick="toggleDayPanel(this)"',
    'function quickCheckin()',
    'function exportData()'
)

foreach ($marker in $required) {
    if (-not $html.Contains($marker)) {
        throw "Missing theme contract marker: $marker"
    }
}

$themeMatch = [regex]::Match($html, '(?is)<style\s+id="animal-island-theme">(.*?)</style>')
if (-not $themeMatch.Success) {
    throw 'Animal Island theme block is missing'
}
$theme = $themeMatch.Groups[1].Value
$themedComponents = @(
    'body', '.header', '.btn', '.progress-card', '.side-nav', '.checkin-card',
    '.phase-card', '.week-card', '.day-card', '.day-note-input', '.resource-tag',
    '.modal-overlay', '.modal', '.toast', ':focus-visible',
    '@media (max-width:900px)', '@media print'
)
foreach ($selector in $themedComponents) {
    if (-not $theme.Contains($selector)) {
        throw "Visible component is outside the unified theme: $selector"
    }
}
foreach ($upstreamColor in @('#19c8b9', '#725d42', '#f0a870', '#fff9e6')) {
    if (-not $theme.Contains($upstreamColor) -and -not $html.Contains($upstreamColor)) {
        throw "Missing Animal Island reference color: $upstreamColor"
    }
}

if ($html -match '--bg:\s*#0f1117|--surface:\s*#1a1d27|--surface2:\s*#22262f') {
    throw 'Legacy dark root palette is still active'
}

if (-not (Test-Path -LiteralPath $assetPath)) {
    throw 'Mascot asset is missing'
}
if (-not (Test-Path -LiteralPath (Join-Path $root 'assets/animal-island/SOURCE.md'))) {
    throw 'Mascot attribution is missing'
}
if ($html -match '(?i)src\s*=\s*["'']https?://|@import\s+url|url\(\s*["'']?https?://') {
    throw 'Page has a remote runtime asset dependency'
}

$styleBlocks = [regex]::Matches($html, '(?is)<style\b[^>]*>(.*?)</style>')
foreach ($style in $styleBlocks) {
    $open = ($style.Groups[1].Value.ToCharArray() | Where-Object { $_ -eq '{' }).Count
    $close = ($style.Groups[1].Value.ToCharArray() | Where-Object { $_ -eq '}' }).Count
    if ($open -ne $close) {
        throw "Unbalanced CSS braces: $open opening, $close closing"
    }
}

$signature = [System.IO.File]::ReadAllBytes($assetPath)[0..7]
$png = [byte[]](0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a)
if (Compare-Object $signature $png) {
    throw 'Mascot asset is not a valid PNG'
}

$runtimeCheck = @'
const fs = require('fs');
const html = fs.readFileSync(process.argv[1], 'utf8');
const start = html.indexOf('<script>');
const end = html.lastIndexOf('</script>');
if (start < 0 || end < start) throw new Error('No executable script found');

const elements = new Map();
const classList = () => {
  const names = new Set();
  return {
    add: (...items) => items.forEach(item => names.add(item)),
    remove: (...items) => items.forEach(item => names.delete(item)),
    toggle: item => names.has(item) ? (names.delete(item), false) : (names.add(item), true),
    contains: item => names.has(item),
  };
};
const element = id => {
  if (!elements.has(id)) elements.set(id, {
    id, value: '', textContent: '', innerHTML: '', style: {}, classList: classList(),
    addEventListener() {}, appendChild() {}, remove() {}, click() {}, scrollIntoView() {},
    querySelector() { return null; },
  });
  return elements.get(id);
};
let ready;
const documentStub = {
  getElementById: element,
  querySelectorAll: () => [],
  createElement: tag => element(`created-${tag}`),
  addEventListener: (type, handler) => { if (type === 'DOMContentLoaded') ready = handler; },
};
const storage = new Map();
const localStorageStub = {
  getItem: key => storage.has(key) ? storage.get(key) : null,
  setItem: (key, value) => storage.set(key, String(value)),
  removeItem: key => storage.delete(key),
};
const script = html.slice(start + '<script>'.length, end);
const api = new Function('document', 'localStorage', 'window', 'confirm', 'setTimeout',
  `${script}\nreturn { D, renderAll, toggleDayPanel, toggleDay, saveNote, updateQuickWeek, updateQuickDayOptions, quickCheckin, openCheckinModal, closeCheckinModal, exportData };`
)(documentStub, localStorageStub, {}, () => true, () => 0);

api.renderAll();
if (!element('contentArea').innerHTML.includes('phase5')) throw new Error('Roadmap did not render all phases');
const panel = { classList: classList() };
api.toggleDayPanel({ nextElementSibling: panel });
if (!panel.classList.contains('open')) throw new Error('Day panel did not expand');
api.toggleDay(0, 0, 0);
const state = JSON.parse(localStorageStub.getItem('ai_roadmap_progress_v2'));
if (!state['0-0-0']?.done) throw new Error('Day completion did not persist');
api.saveNote(0, 0, 0, 'runtime-check');
const noted = JSON.parse(localStorageStub.getItem('ai_roadmap_progress_v2'));
if (noted['0-0-0']?.note !== 'runtime-check') throw new Error('Study note did not persist');
element('quickPhase').value = '1';
api.updateQuickWeek();
element('quickWeek').value = '0';
api.updateQuickDayOptions();
element('quickDay').value = '0';
element('quickHours').value = '2.5';
api.quickCheckin();
const checkins = JSON.parse(localStorageStub.getItem('ai_roadmap_checkins_v2'));
if (checkins.at(-1)?.hours !== 2.5) throw new Error('Quick check-in did not persist');
api.openCheckinModal();
if (!element('checkinModal').classList.contains('show')) throw new Error('Check-in modal did not open');
api.closeCheckinModal();
if (element('checkinModal').classList.contains('show')) throw new Error('Check-in modal did not close');
api.exportData();
if (!element('created-a').download?.startsWith('ai-roadmap-backup-')) throw new Error('Export did not create a backup download');
console.log('Runtime smoke OK');
'@

& node -e $runtimeCheck $htmlPath
if ($LASTEXITCODE -ne 0) {
    throw 'Runtime smoke check failed'
}

'Theme contract OK'
