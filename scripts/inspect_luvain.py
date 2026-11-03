# -*- coding: utf-8 -*-
"""Inspección visual de luvain.it: qué vende, a quién y a qué precio."""
import re
import sys

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
OUT = r"C:\Users\USUARIO\Documents\deepseek-harness\default-workspace\negocio\caza-kit\salidas\luvain.png"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=["--no-sandbox"])
    ctx = b.new_context(locale="it-IT", viewport={"width": 1280, "height": 900}, user_agent=UA)
    pg = ctx.new_page()
    r = pg.goto("https://luvain.it", wait_until="domcontentloaded", timeout=40000)
    pg.wait_for_timeout(6000)
    print("status:", r.status if r else None, "| url final:", pg.url)
    print("title:", pg.title())
    txt = re.sub(r"\s+", " ", pg.inner_text("body"))
    print("largo texto:", len(txt))
    print("\n--- primeros 700 caracteres ---")
    print(txt[:700])
    print("\n--- precios ---", re.findall(r"(?:€|\$)\s?\d{1,4}(?:[.,]\d{2})?", txt)[:8])
    print("--- botones/enlaces ---")
    for e in pg.eval_on_selector_all("a,button", "els => els.slice(0,14).map(e => (e.innerText||'').trim().slice(0,40)).filter(Boolean)"):
        print("   ·", e)
    print("--- hay video:", pg.eval_on_selector_all("video,iframe", "e => e.length"))
    print("--- formularios:", pg.eval_on_selector_all("form", "e => e.length"))
    pg.screenshot(path=OUT)
    print("captura:", OUT)
    b.close()
