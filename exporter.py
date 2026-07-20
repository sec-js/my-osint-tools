#!/usr/bin/env python3
"""
Bookmarklet Exporter - Extract and organize bookmarklets from My OSINT Tools
Extracts bookmarklets from href attributes, organizes by data-folder, and creates
a browser-importable HTML file with proper folder hierarchy.
"""

import re
import requests
import hashlib
from html import unescape
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone
import json


# Version-check bookmarklet injected into the generated HTML file.
# __V__ is replaced with the UTC build timestamp at generation time.
_VERSION_CHECK_JS = (
    "(function(){"
    "var v='__V__';"
    "function p(n){return String(n).padStart(2,'0')}"
    "function fmt(s){var d=new Date(s);"
    "return d.getUTCFullYear()+'-'+p(d.getUTCMonth()+1)+'-'+p(d.getUTCDate())"
    "+' '+p(d.getUTCHours())+':'+p(d.getUTCMinutes())+':'+p(d.getUTCSeconds())+' UTC'}"
    "function gone(){var e=document.getElementById('mot-vm');if(e)e.remove()}"
    "function mkB(t,bg,fg,bc){"
    "var b=document.createElement('button');b.textContent=t;"
    "b.style.cssText='background:'+bg+';color:'+fg+';border:1px solid '+bc"
    "+';padding:8px 18px;border-radius:6px;font-size:13px;font-weight:600;cursor:pointer;';"
    "return b}"
    "function show(ok,remote){"
    "gone();"
    "var m=document.createElement('div');m.id='mot-vm';"
    "m.style.cssText='position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);"
    "background:#022447;color:#FFF;padding:0;border:2px solid #008BC4;border-radius:10px;"
    "z-index:999999;width:420px;max-width:90vw;font-family:Arial,sans-serif;"
    "box-shadow:0 10px 40px rgba(0,0,0,0.6);';"
    "var dh=document.createElement('div');"
    "dh.style.cssText='background:#008BC4;color:#FFF;padding:10px 20px;"
    "border-radius:8px 8px 0 0;text-align:center;font-weight:bold;font-size:13px;position:relative;';"
    "dh.innerHTML='\U0001F516 My OSINT Bookmarklets — Version Check"
    "<div style=\"font-size:9px;color:#00E6F0;margin-top:3px;\">tools.myosint.training</div>';"
    "var x=document.createElement('button');x.innerHTML='×';"
    "x.style.cssText='position:absolute;top:4px;right:10px;background:none;border:none;"
    "color:#FFF;font-size:24px;cursor:pointer;line-height:1;padding:0;';"
    "x.onclick=function(){m.remove()};dh.appendChild(x);m.appendChild(dh);"
    "var bd=document.createElement('div');bd.style.padding='20px';"
    "var ic=document.createElement('div');"
    "ic.style.cssText='text-align:center;font-size:32px;margin-bottom:10px;';"
    "ic.textContent=ok?'✅':'⬆️';bd.appendChild(ic);"
    "var hp=document.createElement('p');"
    "hp.style.cssText='text-align:center;font-size:15px;font-weight:bold;margin-bottom:14px;"
    "color:'+(ok?'#00E6F0':'#ffc107')+';';"
    "hp.textContent=ok?'Your bookmarklets are up to date!':'Updates are available!';bd.appendChild(hp);"
    "var vb=document.createElement('div');"
    "vb.style.cssText='background:#033556;border-radius:6px;padding:10px;font-size:12px;color:#CCC;';"
    "if(ok){vb.innerHTML='Your version:<br>"
    "<strong style=\"color:#FFF;font-family:Courier New,monospace;\">'+fmt(v)+'</strong>'}"
    "else{vb.innerHTML='Your version:<br>"
    "<strong style=\"color:#adb5bd;font-family:Courier New,monospace;\">'+fmt(v)+'</strong>"
    "<br><br>Latest:<br>"
    "<strong style=\"color:#00E6F0;font-family:Courier New,monospace;\">'+fmt(remote)+'</strong>'}"
    "bd.appendChild(vb);"
    "var br=document.createElement('div');"
    "br.style.cssText='margin-top:14px;display:flex;gap:10px;justify-content:center;';"
    "if(!ok){"
    "var dl=mkB('⬇️ Download Update','#008BC4','#FFF','#008BC4');"
    "dl.onclick=function(){"
    "dl.textContent='Downloading...';"
    "fetch('https://tools.myosint.training/myosint_bookmarklets.html',{cache:'no-store'})"
    ".then(function(r){return r.blob()})"
    ".then(function(blob){"
    "var u=URL.createObjectURL(blob);"
    "var a=document.createElement('a');"
    "a.href=u;a.download='myosint_bookmarklets.html';"
    "document.body.appendChild(a);a.click();"
    "document.body.removeChild(a);URL.revokeObjectURL(u);"
    "dl.textContent='⬇️ Download Update'})"
    ".catch(function(){window.open('https://tools.myosint.training/myosint_bookmarklets.html','_blank');"
    "dl.textContent='⬇️ Download Update'});"
    "};"
    "br.appendChild(dl)}"
    "var ob=mkB(ok?'OK':'Not Now','#033556','#CCC','#008BC4');"
    "ob.onclick=function(){m.remove()};br.appendChild(ob);"
    "bd.appendChild(br);m.appendChild(bd);document.body.appendChild(m)}"
    "function err(){"
    "gone();"
    "var m=document.createElement('div');m.id='mot-vm';"
    "m.style.cssText='position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);"
    "background:#022447;color:#FFF;padding:20px;border:2px solid #e04060;border-radius:10px;"
    "z-index:999999;width:380px;max-width:90vw;font-family:Arial,sans-serif;"
    "text-align:center;box-shadow:0 10px 40px rgba(0,0,0,0.6);';"
    "var ed=document.createElement('div');"
    "ed.style.cssText='font-size:28px;margin-bottom:10px;';"
    "ed.textContent='⚠️';m.appendChild(ed);"
    "var ep=document.createElement('p');"
    "ep.style.cssText='color:#ffc107;font-weight:bold;margin-bottom:8px;';"
    "ep.textContent='Could not check for updates';m.appendChild(ep);"
    "var es=document.createElement('p');"
    "es.style.cssText='color:#CCC;font-size:12px;margin-bottom:14px;';"
    "es.textContent='Visit tools.myosint.training to check manually.';m.appendChild(es);"
    "var eb=document.createElement('button');eb.textContent='OK';"
    "eb.style.cssText='background:#033556;color:#CCC;border:1px solid #008BC4;"
    "padding:6px 16px;border-radius:6px;font-size:13px;cursor:pointer;';"
    "eb.onclick=function(){m.remove()};m.appendChild(eb);document.body.appendChild(m)}"
    "fetch('https://tools.myosint.training/version.json',{cache:'no-store'})"
    ".then(function(r){return r.json()})"
    ".then(function(d){show(v>=d.built,d.built)})"
    ".catch(err)"
    "})()"
)


class BookmarkletExporter:
    def __init__(self, url: str):
        self.url = url
        self.bookmarklets: Dict[str, List[dict]] = {}

    def fetch_html(self) -> str:
        """Fetch HTML from the provided URL or file"""
        if self.url.startswith('/') or self.url.startswith('./') or Path(self.url).exists():
            return Path(self.url).read_text(encoding='utf-8')

        print(f"Fetching HTML from {self.url}...")
        response = requests.get(self.url)
        response.raise_for_status()
        return response.text

    def extract_bookmarklets(self, html: str) -> List[dict]:
        """Extract bookmarklets from HTML with their folders and titles"""
        bookmarklets = []

        pattern = r'<a\s+[^>]*?data-folder="([^"]+)"[^>]*?href="([^"]+)"[^>]*?>([^<]+)</a>|<a\s+[^>]*?href="([^"]+)"[^>]*?data-folder="([^"]+)"[^>]*?>([^<]+)</a>'

        matches = re.finditer(pattern, html, re.IGNORECASE | re.DOTALL)

        for match in matches:
            groups = match.groups()
            if groups[0]:  # data-folder before href
                folder_path = groups[0]
                href = groups[1]
                title = groups[2].strip()
            else:  # href before data-folder
                folder_path = groups[4]
                href = groups[3]
                title = groups[5].strip()

            code = unescape(href)

            if code.startswith('javascript:'):
                code = code[len('javascript:'):]

            bookmarklets.append({
                'title': title,
                'code': code,
                'folder': folder_path
            })

        print(f"Extracted {len(bookmarklets)} bookmarklets")
        return bookmarklets

    def organize_by_folder(self, bookmarklets: List[dict]) -> Dict[str, List[dict]]:
        """Organize bookmarklets into nested folder structure"""
        organized = {}

        for bookmark in bookmarklets:
            folder_path = bookmark['folder']
            if folder_path not in organized:
                organized[folder_path] = []
            organized[folder_path].append(bookmark)

        return organized

    def build_nested_structure(self, organized: Dict[str, List[dict]]) -> Dict:
        """Build nested folder/bookmarklet structure"""
        root = {'folders': {}, 'bookmarklets': []}

        for folder_path, bookmarks in organized.items():
            parts = folder_path.split('/')
            current = root['folders']

            for part in parts[:-1]:
                if part not in current:
                    current[part] = {'folders': {}, 'bookmarklets': []}
                current = current[part]['folders']

            final_folder = parts[-1]
            if final_folder not in current:
                current[final_folder] = {'folders': {}, 'bookmarklets': []}

            current[final_folder]['bookmarklets'].extend(bookmarks)

        return root

    def wrap_with_parent_folder(self, structure: Dict, parent_name: str = 'My OSINT Bookmarklets') -> Dict:
        """Wrap entire structure under a parent folder"""
        return {
            'folders': {
                parent_name: structure
            },
            'bookmarklets': []
        }

    def generate_html(self, structure: Dict, iso_datetime: str = None) -> str:
        """Generate browser-importable HTML bookmark file"""
        if iso_datetime is None:
            iso_datetime = datetime.now(timezone.utc).replace(microsecond=0).strftime('%Y-%m-%dT%H:%M:%SZ')

        html_parts = [
            '<!DOCTYPE NETSCAPE-Bookmark-file-1>',
            '<html>',
            '<head>',
            f'<!--\n    This is an auto-generated bookmark file exported from\n    My OSINT Tools (https://tools.myosint.training)\n    Generated at: {iso_datetime}\n-->',
            '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
            '<TITLE>My OSINT Bookmarklets</TITLE>',
            '</head>',
            '<body>',
            '<H1>My OSINT Bookmarklets</H1>',
            '<DL><p>'
        ]

        def add_folder_recursively(folder_dict: Dict, indent: int = 1) -> None:
            indent_str = '    ' * indent

            # Alphabetical, except "Social Media" is always pinned to the top.
            for folder_name, folder_content in sorted(folder_dict['folders'].items(), key=lambda x: (x[0] != 'Social Media', x[0].lower())):
                html_parts.append(f'{indent_str}<DT><H3>{self._escape_html(folder_name)}</H3>')
                html_parts.append(f'{indent_str}<DL><p>')
                add_folder_recursively(folder_content, indent + 1)
                html_parts.append(f'{indent_str}</DL><p>')

            for bookmark in sorted(folder_dict['bookmarklets'], key=lambda b: b['title'].lower()):
                escaped_title = self._escape_html(bookmark['title'])
                escaped_code = self._escape_html(bookmark['code'])

                if not bookmark['code'].startswith('javascript:'):
                    href = f"javascript:{escaped_code}"
                else:
                    href = escaped_code

                html_parts.append(
                    f'{indent_str}<DT><A HREF="{href}">'
                    f'{escaped_title}</A>'
                )

        add_folder_recursively(structure)

        html_parts.extend([
            '</DL><p>',
            '</body>',
            '</html>'
        ])

        return '\n'.join(html_parts)

    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters"""
        return (text.replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;')
                    .replace('"', '&quot;')
                    .replace("'", '&#39;'))

    @staticmethod
    def _compute_content_hash(bookmarklets: List[dict]) -> str:
        """Hash of the extracted bookmarklets' actual content (title/code/folder),
        independent of build time — used to detect whether anything worth a new
        version actually changed, so a run where index.html's bookmarklets are
        unchanged reuses the previous build timestamp and produces byte-identical
        output (nothing for CI to commit)."""
        canonical = json.dumps(
            sorted(
                ({'title': b['title'], 'code': b['code'], 'folder': b['folder']} for b in bookmarklets),
                key=lambda b: (b['folder'], b['title'], b['code'])
            ),
            sort_keys=True
        )
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    @staticmethod
    def _read_previous_version(version_path: Path) -> Optional[dict]:
        """Read a previously-written version.json, if present and well-formed"""
        if not version_path.exists():
            return None
        try:
            return json.loads(version_path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            return None

    def write_version_json(self, iso_datetime: str, content_hash: str, output_path: Path) -> None:
        """Write version.json alongside the generated bookmarks file"""
        version_path = output_path.parent / 'version.json'
        version_path.write_text(
            json.dumps({'built': iso_datetime, 'content_hash': content_hash}, indent=2),
            encoding='utf-8'
        )
        print(f"✅ Written version.json: {iso_datetime}")

    def export(self, output_file: str = 'bookmarklets.html') -> str:
        """Main export method - orchestrates the entire process"""
        # Fetch and parse
        html = self.fetch_html()
        bookmarklets = self.extract_bookmarklets(html)

        if not bookmarklets:
            print("❌ No bookmarklets found!")
            return None

        # Organize
        organized = self.organize_by_folder(bookmarklets)
        print(f"Organized into {len(organized)} folders")

        # Build nested structure
        structure = self.build_nested_structure(organized)

        # Wrap under parent folder
        structure = self.wrap_with_parent_folder(structure)

        # Only mint a new build timestamp if the actual extracted bookmarklet
        # content changed since the last run — otherwise reuse the previous
        # timestamp so this run's output is byte-identical and CI has nothing
        # new to commit (previously every run bumped the timestamp unconditionally,
        # which meant every push to main triggered a follow-up bot commit).
        output_path = Path(output_file)
        version_path = output_path.parent / 'version.json'
        content_hash = self._compute_content_hash(bookmarklets)
        previous = self._read_previous_version(version_path)

        if previous and previous.get('content_hash') == content_hash and previous.get('built'):
            iso_datetime = previous['built']
            print(f"No bookmarklet content changes detected — reusing build timestamp {iso_datetime}")
        else:
            iso_datetime = datetime.now(timezone.utc).replace(microsecond=0).strftime('%Y-%m-%dT%H:%M:%SZ')
            print(f"Bookmarklet content changed — new build timestamp {iso_datetime}")

        # Add version-check bookmark at the end of the "My OSINT Bookmarklets" folder
        version_check_code = _VERSION_CHECK_JS.replace('__V__', iso_datetime)
        version_bookmark = {
            'title': f'v{iso_datetime} - Check for bookmarklet updates',
            'code': version_check_code,
        }
        structure['folders']['My OSINT Bookmarklets']['bookmarklets'].append(version_bookmark)

        # Generate HTML
        bookmark_html = self.generate_html(structure, iso_datetime)

        # Save bookmark HTML
        output_path.write_text(bookmark_html, encoding='utf-8')
        print(f"\n✅ Successfully exported {len(bookmarklets)} bookmarklets")

        # Write version.json alongside the HTML
        self.write_version_json(iso_datetime, content_hash, output_path)

        return str(output_path.absolute())


def main():
    """Main entry point"""
    import sys

    if len(sys.argv) > 1:
        input_source = sys.argv[1]
    else:
        input_source = "index.html"

    exporter = BookmarkletExporter(input_source)
    exporter.export('myosint_bookmarklets.html')


if __name__ == '__main__':
    main()
