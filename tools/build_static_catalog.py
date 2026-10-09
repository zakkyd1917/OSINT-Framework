#!/usr/bin/env python3
"""Generate a usable, fully static HTML catalog. No JavaScript is generated."""
from __future__ import annotations
import html
import json
import pathlib
from urllib.parse import urlsplit

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILE = ROOT / "public" / "index.html"

CSS = """
:root{color-scheme:light;--ink:#202428;--blue:#18384a;--gray:#66747c;--paper:#f5f1e8}
*{box-sizing:border-box}body{font:16px/1.55 'IBM Plex Serif',Georgia,serif;color:var(--ink);background:var(--paper);margin:0}
main{max-width:1130px;margin:auto;padding:2.3rem 2rem 5rem}
h1,h2,h3{line-height:1.25;color:var(--blue)}h1{font-size:2.1rem}h2{margin-top:2.4rem;border-top:1px solid #b8b4aa;padding-top:1.3rem}
h3{font-size:1.03rem}p{max-width:85ch}a{color:#145273;text-decoration-thickness:1px;text-underline-offset:.15em}
header{border-bottom:3px solid var(--blue)}header p{color:var(--gray)}
nav{display:flex;gap:.4rem 1.1rem;flex-wrap:wrap;font-size:.92rem;border-bottom:1px solid #bbb;padding:1rem 0 1.4rem}
section{scroll-margin-top:2rem}details{margin:.35rem 0 0 1rem}details>summary{cursor:pointer;font-weight:600;color:var(--blue)}
ul{list-style:none;padding:0 0 0 .7rem}li.tool{border-left:2px solid #b9c2c6;margin:.7rem 0;padding:0 .9rem}
.name{font-weight:600}.metadata{font:12px/1.5 Arial,sans-serif;color:var(--gray);margin:.2rem 0}
.description{margin:.15rem 0 .4rem;font-size:.93rem;max-width:96ch}
.notice{padding:1rem 0;border-bottom:1px solid #b8b4aa}small{color:var(--gray)}
@media(max-width:650px){main{padding:1.1rem 1rem 3rem}h1{font-size:1.65rem}details{margin-left:.3rem}}
@media print{nav{display:none}details{display:block}li.tool{break-inside:avoid}a{color:inherit}}
"""
def e(s):
    return html.escape(str(s or ""), quote=True)
def name_id(s):
    return "cat-" + "".join(x.lower() if x.isalnum() else "-" for x in s).strip("-")
def render(node):
    if isinstance(node.get("children"), list):
        if not node["children"]:
            return ""
        out = ["<details open><summary>"+e(node["name"])+"</summary><ul>"]
        out += ["<li>"+render(x)+"</li>" for x in node["children"]]
        out.append("</ul></details>")
        return "".join(out)
    url = node.get("url","")
    kind = urlsplit(url).scheme
    # Do not generate clickable non-HTTPS or executable bookmarklets.
    link = ('<a href="'+e(url)+'" rel="noopener noreferrer" target="_blank">'+e(node.get("name"))+"</a>"
            if kind == "https" else e(node.get("name")) + " (manual review required)")
    observed = node.get("verification",{}).get("lastChecked") or "not independently checked"
    access = node.get("access",{})
    cost = access.get("costModel","unassessed")
    return ('<article class="tool"><div class="name">'+link+'</div>'
            '<div class="metadata">Status: '+e(node.get("status","unverified"))+
            ' · Cost: '+e(cost)+' · Last observation: '+e(observed)+'</div>'
            '<p class="description">'+e(node.get("description",""))+'</p>'
            +('<p class="description"><strong>Caution:</strong> '+e(node.get("editorialCaution"))+'</p>'
              if node.get("editorialCaution") else "")+"</article>")
def main():
    root=json.loads((ROOT/"public"/"arf.json").read_text(encoding="utf-8"))
    cats=root.get("children",[])
    nav="".join('<a href="#'+name_id(x["name"])+'">'+e(x["name"])+"</a>" for x in cats)
    content="".join('<section id="'+name_id(x["name"])+'"><h2>'+e(x["name"])+'</h2>'
                    +render(x)+"</section>" for x in cats)
    page=('<!doctype html><html lang="en"><head><meta charset="utf-8">'
          '<meta name="viewport" content="width=device-width,initial-scale=1">'
          '<meta name="referrer" content="no-referrer">'
          '<title>OSINT Evidence Catalog</title><style>'+CSS+'</style></head>'
          '<body><main><header><h1>OSINT Evidence Catalog</h1>'
          '<p>An independent research-resource index. Resource claims are unverified '
          'unless accompanied by dated observations. No JavaScript is executed.</p></header>'
          '<p class="notice"><strong>Interpretation:</strong> A reachable website is not '
          'proof of functionality, accuracy, affordability, anonymity, or fitness for '
          'investigative use. Use browser Find to search this static directory.</p>'
          '<nav aria-label="Categories">'+nav+'</nav>'+content
          '<footer><small>MIT-licensed code and data adaptations retain original '
          'license notices. See the repository license for attribution.</small></footer>'
          '</main></body></html>')
    FILE.write_text(page,encoding="utf-8")
    print("Generated "+str(FILE)+" ("+str(len(page))+" bytes)")
if __name__=="__main__":
    main()
