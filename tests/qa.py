"""QA suite for the tutorial site. Run from the repository root:
     pip install playwright && playwright install chromium
     python tests/qa.py            (optional: AXE=/path/to/axe.min.js for accessibility checks)
"""
import http.server, threading, functools, os, re, sys, json
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.environ.get("SHOTS", "/tmp/shots"); os.makedirs(SHOTS, exist_ok=True)
AXE = os.environ.get("AXE")
h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
h.log_message = lambda *a: None
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f"http://127.0.0.1:{srv.server_port}/"
fails, passes = [], 0
def check(name, ok, detail=""):
    global passes
    if ok: passes += 1
    else: fails.append(f"{name} {detail}")
    print(("PASS " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))

VIEWPORTS = {"desktop": (1440, 900), "laptop": (1100, 760), "tablet": (768, 1024), "mobile": (390, 844), "small-mobile": (320, 640)}
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, (w, hgt) in VIEWPORTS.items():
        ctx = b.new_context(viewport={"width": w, "height": hgt}, reduced_motion="reduce")
        pg = ctx.new_page(); errs = []; bad = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)  # local 404s are caught by the response check
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("response", lambda r: bad.append(r.url) if r.status >= 400 and URL in r.url else None)
        pg.goto(URL, wait_until="load")
        check(f"{name}: no script errors", not errs, str(errs))
        check(f"{name}: no missing local files", not bad, str(bad))
        over = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
        check(f"{name}: no horizontal page scroll", over <= 0, f"{over}px")
        clipped = pg.evaluate("""() => [...document.querySelectorAll('h1,h2,h3,p,li,dd,a.btn,figcaption')].filter(e => {
            if (e.closest('.figure-plate') || e.closest('.nav')) return false;
            const r = e.getBoundingClientRect(); return r.width && (r.right > innerWidth + 1 || r.left < -1);}).map(e => e.textContent.slice(0,40))""")
        check(f"{name}: no text runs off screen", not clipped, str(clipped))
        imgs = pg.evaluate("[...document.images].filter(i => !i.complete || !i.naturalWidth).map(i => i.src)")
        check(f"{name}: all images load", not imgs, str(imgs))
        pg.screenshot(path=f"{SHOTS}/{name}-top.png")
        pg.screenshot(path=f"{SHOTS}/{name}-full.png", full_page=True)
        if name == "desktop":
            # content integrity
            html = pg.content()
            ids = set(pg.evaluate("[...document.querySelectorAll('[id]')].map(e => e.id)"))
            anchors = pg.evaluate("[...document.querySelectorAll('a[href^=\"#\"]')].map(a => a.getAttribute('href').slice(1))")
            check("every in-page link has a target", all(a in ids for a in anchors), str([a for a in anchors if a not in ids]))
            mins = [int(x) for x in re.findall(r"<span>(\d+) minutes</span>", html)]
            check("programme parts sum to 150 minutes", sum(mins) == 150 and len(mins) == 6, str(mins))
            starts = re.findall(r"<b>(\d):(\d\d)</b>", html); t = 0; ok = True
            for (hh, mm), m in zip(starts, mins):
                ok &= int(hh) * 60 + int(mm) == t; t += m
            check("start offsets agree with durations", ok)
            check("one h1", pg.locator("h1").count() == 1)
            check("nine references", pg.locator(".refs li").count() == 9)
            ext = pg.evaluate("[...document.querySelectorAll('a[href^=\"http\"]')].map(a => a.href)")
            check("external links are https", all(u.startswith("https://") for u in ext))
            # interactive figure: values verified against Ripser for this point cloud
            def state(eps):
                pg.evaluate("""v => {const s=document.getElementById('eps'); s.value=v; s.dispatchEvent(new Event('input',{bubbles:true}))}""", eps)
                return (int(pg.inner_text("#out-b0")), int(pg.inner_text("#out-b1")),
                        pg.locator("#complex line[visibility=visible]").count(), pg.locator("#complex polygon[visibility=visible]").count())
            s0 = state(0); check("eps=0: 26 components, no loops, no edges", s0 == (26, 0, 0, 0), str(s0))
            s1 = state(0.7); check("eps=0.70: both rings detected (two loops)", s1[1] == 2, str(s1))
            s2 = state(1.2); check("eps=1.20: one component, large ring only", s2[:2] == (1, 1), str(s2))
            s3 = state(1.75); check("eps=1.75: all loops filled", s3[:2] == (1, 0) and s3[2] > s2[2] and s3[3] > s2[3], str(s3))
            pg.focus("#eps"); pg.keyboard.press("Home"); pg.keyboard.press("ArrowRight")
            check("slider works from the keyboard", pg.inner_text("#out-eps") == "0.01", pg.inner_text("#out-eps"))
            check("slider announces state", "components" in pg.get_attribute("#eps", "aria-valuetext"))
            if AXE:
                pg.add_script_tag(path=AXE)
                res = pg.evaluate("axe.run(document,{runOnly:['wcag2a','wcag2aa','best-practice']}).then(r=>r.violations.map(v=>[v.id,v.impact,v.nodes.length,v.nodes[0].html.slice(0,90)]))")
                check("axe: no accessibility violations (WCAG 2 A/AA + best practice)", not res, json.dumps(res))
        ctx.close()
    # motion path: animation plays once on load and can be paused
    ctx = b.new_context(viewport={"width": 1280, "height": 800}); pg = ctx.new_page(); pg.goto(URL)
    pg.wait_for_timeout(900)
    v = float(pg.input_value("#eps")); check("load animation advances the scale", 0 < v < 1.75, str(v))
    check("button reads Pause while playing", pg.inner_text("#play") == "Pause")
    pg.click("#play"); v1 = float(pg.input_value("#eps")); pg.wait_for_timeout(300)
    check("pause holds the scale", float(pg.input_value("#eps")) == v1 and pg.inner_text("#play") == "Play")
    pg.screenshot(path=f"{SHOTS}/desktop-motion.png")
    # keyboard: first Tab reveals the skip link
    pg.reload(); pg.keyboard.press("Tab")
    check("skip link is first focus stop", pg.evaluate("document.activeElement.className") == "skip")
    ctx.close(); b.close()
print(f"\n{passes} passed, {len(fails)} failed"); sys.exit(1 if fails else 0)
