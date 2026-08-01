from pathlib import Path
import re

BASE_PATH = Path('templates/base.html')
STYLE_PATH = Path('static/css/style.css')

BASE_CONTENT = '''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="theme-color" content="#5f7ea8">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="sabrmarkze">
  <title>{% block title %}Sabr Central{% endblock %}</title>
  <link rel="manifest" href="{{ url_for('static', filename='manifest.webmanifest') }}">
  <link rel="icon" href="{{ url_for('static', filename='icons/icon.svg') }}" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Amiri:wght@400;700&family=Cairo:wght@400;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
  {% block head_extra %}{% endblock %}
</head>
<body>
  {% block content %}{% endblock %}
  <script src="{{ url_for('static', filename='js/pwa.js') }}"></script>
  {% block scripts %}{% endblock %}
</body>
</html>
'''

STYLE_CONTENT = '''/* Shared responsive theme for Sabr Central */
:root {
  --bg: #f4f7fb;
  --bg-soft: #eef3f8;
  --surface: rgba(255, 255, 255, 0.88);
  --surface-strong: #ffffff;
  --primary: #5f7ea8;
  --primary-dark: #486281;
  --accent: #8aa6c1;
  --success: #2e7d32;
  --success-bg: #eaf6ec;
  --danger: #d9534f;
  --danger-dark: #b03a37;
  --text: #1f2d3d;
  --muted: #6b7b8c;
  --border: #dce5ee;
  --radius: 18px;
  --shadow: 0 14px 32px rgba(57, 82, 110, 0.10);
  --max-width: 1240px;
}

* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  min-height: 100vh;
  direction: rtl;
  font-family: "Cairo", "Amiri", "Arial", sans-serif;
  color: var(--text);
  background:
    radial-gradient(circle at top right, rgba(138, 166, 193, 0.16), transparent 28%),
    radial-gradient(circle at bottom left, rgba(95, 126, 168, 0.12), transparent 26%),
    linear-gradient(180deg, #f7f9fc 0%, #eef3f8 100%);
  line-height: 1.6;
}

img,
svg,
iframe {
  max-width: 100%;
  height: auto;
}

button,
input,
select,
textarea {
  font: inherit;
}

.container {
  width: min(100%, var(--max-width));
  margin: 0 auto;
  padding: 32px 20px 40px;
}

.page-title,
.page-heading,
h1,
h2,
h3,
h4,
h5,
h6 {
  margin: 0 0 14px;
  font-weight: 700;
  color: var(--primary-dark);
}

.page-title {
  font-size: clamp(2rem, 2.5vw, 2.6rem);
  text-align: center;
}

.subtitle,
.page-description,
.description,
.help-text {
  max-width: 920px;
  margin: 0 auto 24px;
  color: var(--muted);
  line-height: 1.8;
  text-align: center;
  font-size: 1rem;
}

.cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 22px;
  margin-top: 24px;
}

.card {
  background: var(--surface);
  border: 1px solid rgba(220, 229, 238, 0.95);
  border-radius: var(--radius);
  padding: 24px;
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 18px;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.card:hover {
  transform: translateY(-3px);
  box-shadow: 0 20px 40px rgba(57, 82, 110, 0.14);
}

.panel,
.form-card,
.card-panel,
.table-card,
.chart-card,
.status-card,
.modal-content,
.toolbar,
.form-section,
.certificate-toolbar {
  background: var(--surface);
  border: 1px solid rgba(220, 229, 238, 0.9);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 24px;
}

.panel {
  margin-top: 20px;
}

.flash-messages,
.message-list,
.alerts {
  margin-bottom: 18px;
}

.flash,
.msg,
.alert {
  padding: 14px 16px;
  border-radius: 14px;
  margin-bottom: 14px;
  border: 1px solid transparent;
  font-weight: 700;
}

.flash.success,
.msg.success,
.alert-success {
  color: var(--success);
  background: var(--success-bg);
  border-color: rgba(46, 125, 50, 0.18);
}

.flash.error,
.msg.error,
.alert-danger {
  color: var(--danger-dark);
  background: #fff1f1;
  border-color: rgba(217, 83, 79, 0.18);
}

.flash.info,
.msg.info,
.alert-info {
  color: #35567a;
  background: #eef5fb;
  border-color: #d6e6f5;
}

form {
  display: grid;
  gap: 20px;
}

.form-grid,
.info-grid,
.grid-two,
.grid-three,
.grid-four {
  display: grid;
  gap: 18px;
}

.form-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.info-grid,
.grid-two {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.grid-three {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.grid-four {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.form-group,
.field,
.filter-group,
.select-group {
  display: grid;
  gap: 10px;
}

label {
  display: block;
  color: var(--primary-dark);
  font-weight: 700;
  font-size: 0.98rem;
}

input[type="text"],
input[type="password"],
input[type="date"],
input[type="file"],
select,
textarea {
  width: 100%;
  min-height: 46px;
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 14px 16px;
  background: #fbfdff;
  color: var(--text);
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

textarea {
  min-height: 120px;
  resize: vertical;
}

input:focus,
select:focus,
textarea:focus {
  border-color: rgba(95, 126, 168, 0.55);
  box-shadow: 0 0 0 4px rgba(95, 126, 168, 0.12);
  background: #fff;
}

select {
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
}

button,
.btn,
a.button,
a.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  text-decoration: none;
  border: none;
  cursor: pointer;
  border-radius: 14px;
  font-weight: 700;
  font-size: 0.95rem;
  color: #fff;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  box-shadow: 0 12px 26px rgba(95, 126, 168, 0.2);
  padding: 12px 18px;
  transition: transform 0.2s ease, box-shadow 0.2s ease, filter 0.2s ease;
}

button:hover,
.btn:hover,
a.btn:hover,
a.button:hover {
  transform: translateY(-1px);
  filter: brightness(1.03);
  box-shadow: 0 16px 32px rgba(95, 126, 168, 0.25);
}

.btn-danger,
.button-danger {
  background: linear-gradient(135deg, #d9534f 0%, #b03a37 100%);
}

.btn-success,
.button-success {
  background: linear-gradient(135deg, #2e7d32 0%, #1f5c27 100%);
}

.btn-secondary,
.button-secondary,
.link-pill,
.back-link a,
.logout,
.link-button {
  background: rgba(95, 126, 168, 0.12);
  color: var(--primary-dark);
  box-shadow: none;
}

.back-link,
.link-row,
.btn-row,
.toolbar,
.actions,
.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.back-link {
  margin-top: 20px;
}

.back-link a,
.logout,
.link-pill,
.link-button {
  border: 1px solid rgba(95, 126, 168, 0.18);
  padding: 10px 16px;
  border-radius: 999px;
}

.logout:hover,
.back-link a:hover,
.link-button:hover,
.link-pill:hover {
  background: rgba(95, 126, 168, 0.16);
  transform: translateY(-1px);
}

.table-wrap {
  width: 100%;
  overflow-x: auto;
  border-radius: 18px;
  border: 1px solid rgba(220, 229, 238, 0.95);
  box-shadow: var(--shadow);
  background: var(--surface-strong);
}

table {
  width: 100%;
  border-collapse: collapse;
  min-width: 700px;
  background: #fff;
}

thead th,
tbody td,
tfoot th {
  padding: 14px 16px;
  font-size: 0.95rem;
  color: var(--text);
}

thead th {
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  color: #fff;
  text-align: right;
  white-space: nowrap;
}

tbody tr {
  border-top: 1px solid #edf2f7;
}

tbody tr:nth-child(even) {
  background: #f9fbfe;
}

tbody td {
  border-top: 1px solid #edf2f7;
}

tbody tr:hover {
  background: #f2f7fc;
}

td a,
th a {
  color: var(--primary-dark);
  text-decoration: none;
}

td a:hover,
th a:hover {
  text-decoration: underline;
}

.info-item,
.stat,
.card-item,
.detail-box,
.hero-card,
.stat-card {
  background: #f8fbff;
  border: 1px solid #e3ecf7;
  border-radius: 14px;
  padding: 16px;
}

.info-item strong,
.stat-title {
  color: var(--primary-dark);
}

.stat-title {
  display: block;
  font-size: 0.85rem;
  letter-spacing: 0.02em;
  margin-bottom: 8px;
  color: #6b7b8c;
}

.stat-value,
.value {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--primary-dark);
}

.chart-head,
.table-head,
.card-head,
.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.chart-head h2,
.table-head h2,
.card-head h2,
.panel-head h2 {
  margin: 0;
  font-size: 1.1rem;
}

.hint {
  color: var(--muted);
  font-size: 0.92rem;
}

.modal {
  position: fixed;
  inset: 0;
  display: none;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.45);
  z-index: 999;
  padding: 20px;
}

.modal.active {
  display: flex;
}

.modal-content {
  width: min(100%, 520px);
  background: var(--surface-strong);
  border-radius: var(--radius);
  padding: 22px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}

.modal-close {
  border: none;
  background: transparent;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--primary-dark);
}

.text-right {
  text-align: right;
}

.text-center {
  text-align: center;
}

.status-card {
  padding: 24px;
}

@media (max-width: 1024px) {
  .container {
    padding: 28px 18px 34px;
  }

  .form-grid,
  .info-grid,
  .grid-two,
  .grid-three,
  .grid-four {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .container {
    padding: 24px 16px 30px;
  }

  .panel,
  .form-card,
  .table-card,
  .chart-card,
  .status-card,
  .modal-content,
  .certificate-toolbar {
    padding: 20px;
  }

  .cards,
  .toolbar,
  .actions,
  .btn-row,
  .back-link,
  .link-row,
  .action-row {
    display: grid;
    gap: 14px;
  }

  .btn,
  .button,
  a.btn,
  a.button {
    width: 100%;
  }

  table {
    min-width: 0;
  }
}

@media (max-width: 640px) {
  .container {
    padding: 20px 14px 24px;
  }

  .page-title {
    font-size: 1.9rem;
  }

  .panel,
  .form-card,
  .table-card,
  .chart-card,
  .status-card,
  .modal-content,
  .certificate-toolbar {
    padding: 18px;
  }

  .table-wrap {
    border-radius: 14px;
  }

  table,
  thead,
  tbody,
  th,
  td,
  tr {
    display: block;
  }

  thead tr {
    position: absolute;
    top: -9999px;
    left: -9999px;
  }

  tr {
    margin-bottom: 14px;
    border: 1px solid rgba(220, 229, 238, 0.95);
    border-radius: 16px;
    background: #fff;
    padding: 14px 16px;
  }

  td {
    position: relative;
    padding: 10px 16px 10px 110px;
    text-align: right;
    border: none;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 8px;
  }

  td::before {
    position: absolute;
    top: 10px;
    right: 16px;
    width: 88px;
    white-space: nowrap;
    font-weight: 700;
    color: var(--muted);
  }
}
'''

COMMON_HEAD_PATTERNS = [
    r'<title>.*?</title>',
    r'<meta[^>]*charset[^>]*?>',
    r'<meta[^>]*name=["\']viewport["\'][^>]*?>',
    r'<meta[^>]*name=["\']theme-color["\'][^>]*?>',
    r'<meta[^>]*name=["\']apple-mobile-web-app-capable["\'][^>]*?>',
    r'<meta[^>]*name=["\']apple-mobile-web-app-title["\'][^>]*?>',
    r'<link[^>]*rel=["\']manifest["\'][^>]*?>',
    r'<link[^>]*rel=["\']icon["\'][^>]*?>',
    r'<link[^>]*href=["\'][^"\']*googleapis[^"\']*["\'][^>]*?>',
    r'<link[^>]*href=["\']{{\s*url_for\(\s*\'static\'\s*,\s*filename\s*=\s*\'css/style\.css\'\s*\)\s*}}["\'][^>]*?>',
    r'<link[^>]*rel=["\']stylesheet["\'][^>]*href=["\'][^"\']*style\.css["\'][^>]*?>',
    r'<link[^>]*rel=["\']preconnect["\'][^>]*?>',
]


def normalize_head_extra(text: str) -> str:
    result = text
    result = re.sub(r'<!DOCTYPE html[^>]*>\s*<html[^>]*>\s*<head[^>]*>', '', result, flags=re.I|re.S)
    result = re.sub(r'</head>\s*$', '', result, flags=re.I|re.S)
    result = re.sub(r'<html[^>]*>', '', result, flags=re.I|re.S)
    result = re.sub(r'</html>', '', result, flags=re.I|re.S)
    result = re.sub(r'<head[^>]*>', '', result, flags=re.I|re.S)
    result = re.sub(r'<body[^>]*>', '', result, flags=re.I|re.S)
    result = re.sub(r'</body>', '', result, flags=re.I|re.S)
    for pat in COMMON_HEAD_PATTERNS:
        result = re.sub(pat, '', result, flags=re.I|re.S)
    result = result.strip()
    return result


def extract_scripts(body: str) -> tuple[str, str]:
    scripts = re.findall(r'<script\b[^>]*?>.*?</script>', body, flags=re.I|re.S)
    filtered = [s for s in scripts if 'pwa.js' not in s]
    body = re.sub(r'<script\b[^>]*?>.*?</script>', '', body, flags=re.I|re.S)
    return body.strip(), '\n'.join(filtered).strip()


if __name__ == '__main__':
    BASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    BASE_PATH.write_text(BASE_CONTENT, encoding='utf-8')
    STYLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STYLE_PATH.write_text(STYLE_CONTENT, encoding='utf-8')

    for path in sorted(Path('templates').glob('*.html')):
        if path.name == 'base.html':
            continue
        text = path.read_text(encoding='utf-8')
        if '{% extends "base.html" %}' in text:
            title_match = re.search(r'{% block title %}(.*?){% endblock %}', text, flags=re.S)
            title_text = title_match.group(1).strip() if title_match else 'Sabr Central'
            head_extra_match = re.search(r'{% block head_extra %}(.*?){% endblock %}', text, flags=re.S)
            content_match = re.search(r'{% block content %}(.*?){% endblock %}', text, flags=re.S)
            scripts_match = re.search(r'{% block scripts %}(.*?){% endblock %}', text, flags=re.S)
            head_extra_raw = head_extra_match.group(1) if head_extra_match else ''
            styles = re.findall(r'<style[^>]*?>.*?</style>', head_extra_raw, flags=re.S)
            head_extra = '\n'.join(styles).strip()
            content_raw = content_match.group(1) if content_match else ''
            content_fixed = re.sub(r'^.*?</head>', '', content_raw, flags=re.S).strip()
            content_fixed = re.sub(r'<body[^>]*>', '', content_fixed, flags=re.I)
            content_fixed = re.sub(r'</body>', '', content_fixed, flags=re.I)
            content_fixed = re.sub(r'</html>', '', content_fixed, flags=re.I)
            content_fixed = content_fixed.strip()
            scripts = scripts_match.group(1).strip() if scripts_match else ''
            new_parts = [
                '{% extends "base.html" %}',
                '{% block title %}' + title_text + '{% endblock %}',
                '{% block head_extra %}',
                head_extra,
                '{% endblock %}',
                '{% block content %}',
                content_fixed,
                '{% endblock %}',
            ]
            if scripts:
                new_parts.extend(['{% block scripts %}', scripts, '{% endblock %}'])
            path.write_text('\n'.join([part for part in new_parts if part is not None]), encoding='utf-8')
            print(f'rewrote {path} (processed base template)')
            continue
        m_body = re.search(r'<body[^>]*>', text, flags=re.I)
        m_body_close = re.search(r'</body>', text, flags=re.I)
        if not m_body or not m_body_close:
            print(f'skip {path} no body tags')
            continue
        head = text[:m_body.start()]
        body = text[m_body.end():m_body_close.start()]
        title_match = re.search(r'<title>(.*?)</title>', head, flags=re.I|re.S)
        title_text = title_match.group(1).strip() if title_match else 'Sabr Central'
        head_extra = normalize_head_extra(head)
        body, scripts = extract_scripts(body)
        new_parts = [
            '{% extends "base.html" %}',
            '{% block title %}' + title_text + '{% endblock %}',
            '{% block head_extra %}',
            head_extra,
            '{% endblock %}',
            '{% block content %}',
            body,
            '{% endblock %}',
        ]
        if scripts:
            new_parts.extend(['{% block scripts %}', scripts, '{% endblock %}'])
        path.write_text('\n'.join([part for part in new_parts if part is not None]), encoding='utf-8')
        print(f'rewrote {path} (converted raw template)')
