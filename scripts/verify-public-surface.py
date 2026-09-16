from html.parser import HTMLParser
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
html_path = root / "docs" / "index.html"
readme_path = root / "README.md"
buyer_path = root / "BUYER-OVERVIEW.md"

html = html_path.read_text(encoding="utf-8")
readme = readme_path.read_text(encoding="utf-8")
buyer = buyer_path.read_text(encoding="utf-8")
checks = []

def check(condition, message):
    if not condition:
        raise AssertionError(message)
    checks.append(message)

check('id="acquisition"' in html, "acquisition section present")
check("Strategic acquisition / licensing" in html, "primary acquisition CTA present")
check("BUYER-OVERVIEW.md" in html and "BUYER-OVERVIEW.md" in readme, "buyer overview linked")
check(html.index('id="acquisition"') < html.index('id="pricing"'), "acquisition precedes pricing")
check("https://rockinai88.github.io/engineering-twin/" in html, "canonical public URL present")
check("../LICENSE.md" not in html and "../SECURITY.md" not in html, "no broken parent-doc links")

ids = re.findall(r'\bid="([^"]+)"', html)
check(len(ids) == len(set(ids)), "HTML ids are unique")
for fragment in re.findall(r'href="#([^"]+)"', html):
    check(fragment in ids, f"anchor target exists: #{fragment}")

class StrictParser(HTMLParser):
    void = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__()
        self.stack = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.void:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1] != tag:
            raise AssertionError(f"HTML nesting mismatch at </{tag}>")
        self.stack.pop()

parser = StrictParser()
parser.feed(html)
parser.close()
check(not parser.stack, f"HTML tags closed: {parser.stack}")

for ref in re.findall(r'(?:src|href)="([^"]+)"', html):
    if ref.startswith(("http://", "https://", "#", "mailto:")):
        continue
    target = (html_path.parent / ref).resolve()
    check(target.exists(), f"local reference exists: {ref}")

for marker in ("€80k", "DR-17", "Holdback", "[BUILD-SHA]", "Treuhänder"):
    check(marker not in html and marker not in readme and marker not in buyer, f"private marker absent: {marker}")

for marker in ("TBD", "TODO", "EINTRAGEN", "[ ]"):
    check(marker not in buyer, f"buyer overview has no placeholder: {marker}")

check((root / "LICENSE.md").exists(), "license file exists")
check((root / "SECURITY.md").exists(), "security file exists")
check("not a binding legal offer" in buyer, "buyer overview carries non-binding notice")

print(f"PUBLIC_SURFACE_PASS checks={len(checks)}")
