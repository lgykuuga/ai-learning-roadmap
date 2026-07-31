# Animal Island Roadmap Theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restyle `ai-learning-roadmap.html` with a complete, locally runnable Animal Island visual system while preserving every existing roadmap interaction.

**Architecture:** Keep the current static HTML, data model, render functions, and localStorage keys. Add one late-cascade theme stylesheet, a compact decorative header layer, and one locally stored upstream mascot image; verify both theme markers and preserved behavior with a standalone PowerShell check.

**Tech Stack:** HTML5, CSS custom properties, vanilla JavaScript, PowerShell verification

---

### Task 1: Add the failing theme contract

**Files:**
- Create: `tests/verify-theme.ps1`
- Test: `ai-learning-roadmap.html`

- [x] **Step 1: Write the failing check**

```powershell
$html = Get-Content -Raw -Encoding UTF8 "$PSScriptRoot/../ai-learning-roadmap.html"
$required = @(
  'id="animal-island-theme"',
  '--island-primary: #19c8b9',
  '--island-paper: #fff8e8',
  'class="header-mascot"',
  'assets/animal-island/animal-icon.png',
  "const STORAGE_KEY = 'ai_roadmap_progress_v2'",
  'function renderAll()',
  'function quickCheckin()',
  'function exportData()'
)
foreach ($marker in $required) {
  if (-not $html.Contains($marker)) { throw "Missing theme contract marker: $marker" }
}
if ($html -match '#0f1117|#1a1d27|#22262f') { throw 'Legacy dark palette is still active' }
if (-not (Test-Path "$PSScriptRoot/../assets/animal-island/animal-icon.png")) { throw 'Mascot asset is missing' }
'Theme contract OK'
```

- [x] **Step 2: Run the check and confirm the red state**

Run: `powershell -NoProfile -ExecutionPolicy Bypass -File tests/verify-theme.ps1`

Expected: FAIL with `Missing theme contract marker: id="animal-island-theme"`.

### Task 2: Add the local theme asset and provenance

**Files:**
- Create: `assets/animal-island/animal-icon.png`
- Create: `assets/animal-island/SOURCE.md`

- [x] **Step 1: Download only the mascot used by the page**

Run:

```powershell
New-Item -ItemType Directory -Force assets/animal-island | Out-Null
curl.exe -L --fail --connect-timeout 10 --max-time 60 `
  https://raw.githubusercontent.com/guokaigdg/animal-island-ui/main/demo/img/animal_icon.png `
  -o assets/animal-island/animal-icon.png
```

Expected: a non-empty PNG with the `89 50 4E 47` signature.

- [x] **Step 2: Record source and license link**

```markdown
# Asset source

`animal-icon.png` comes from [guokaigdg/animal-island-ui](https://github.com/guokaigdg/animal-island-ui), path `demo/img/animal_icon.png`.
See the upstream repository for its current license and attribution terms.
```

### Task 3: Apply one unified late-cascade theme

**Files:**
- Modify: `ai-learning-roadmap.html:7-124`
- Modify: `ai-learning-roadmap.html:128-142`

- [x] **Step 1: Replace the legacy root palette with the shared theme tokens**

```css
:root {
  --island-primary: #19c8b9;
  --island-primary-deep: #0d756e;
  --island-paper: #fff8e8;
  --island-paper-strong: #fffdf5;
  --island-ink: #725d42;
  --island-muted: #8e785d;
  --island-line: #dfc9a8;
  --island-coral: #f0a870;
  --island-leaf: #83b66f;
  --island-shadow: #c9aa7d;
  --bg: var(--island-paper);
  --surface: var(--island-paper-strong);
  --surface2: #f7ebd2;
  --border: var(--island-line);
  --text: var(--island-ink);
  --text2: var(--island-muted);
  --text3: #aa9275;
  --accent: var(--island-primary-deep);
  --accent2: var(--island-primary);
  --green: var(--island-leaf);
  --yellow: #dca94f;
  --orange: var(--island-coral);
  --red: #d9786f;
  --purple: #9d82b5;
  --cyan: var(--island-primary);
  --radius: 22px;
  --radius-sm: 14px;
  --shadow: 0 6px 0 var(--island-shadow), 0 12px 28px rgba(114, 93, 66, .12);
}
```

- [x] **Step 2: Add `#animal-island-theme` after the current stylesheet**

The late stylesheet must style `body`, `.header`, `.btn`, `.main`, `.sidebar`, `.progress-card`, `.side-nav`, `.checkin-card`, `.phase-card`, `.week-card`, `.day-card`, form controls, `.modal`, `.toast`, resource tags, hover/focus/active states, mobile layout, reduced motion, and print mode from the tokens above. Cards use a visible lower edge and 18–24px radii; buttons translate down on `:active`; all focusable controls use a two-pixel aqua outline.

- [x] **Step 3: Add the mascot and semantic header copy**

```html
<div class="header-art" aria-hidden="true">
  <span class="leaf leaf-one"></span>
  <span class="leaf leaf-two"></span>
  <img class="header-mascot" src="assets/animal-island/animal-icon.png" alt="">
</div>
```

Keep the existing title, subtitle, and button handlers unchanged.

### Task 4: Verify behavior and visual consistency

**Files:**
- Test: `tests/verify-theme.ps1`
- Test: `ai-learning-roadmap.html`

- [x] **Step 1: Run the static contract**

Run: `powershell -NoProfile -ExecutionPolicy Bypass -File tests/verify-theme.ps1`

Expected: `Theme contract OK`.

- [ ] **Step 2: Run local browser verification**

Open `ai-learning-roadmap.html` locally and verify at desktop and mobile widths: no horizontal overflow; all cards, controls, modal and toast share the theme; phase/week/day expansion works; a day can be marked complete; a note survives reload; modal opens/closes; export creates JSON.

- [x] **Step 3: Check UTF-8 text integrity**

Run: `rg -n "锟|烫烫|屯屯|ï¿½|�" ai-learning-roadmap.html`

Expected: no output.
