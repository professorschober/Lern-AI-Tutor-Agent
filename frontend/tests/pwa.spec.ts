import { test, expect } from '@playwright/test'

test('Produktions-PWA: Manifest, Offline-Shell und kein API-Cache',async({page})=>{
  await page.goto('http://127.0.0.1:8000/')
  await expect(page.getByRole('heading',{name:'SQL verstehen. Selbstständig anwenden.'})).toBeVisible()
  const manifest = await page.evaluate(async()=>{
    const href = document.querySelector<HTMLLinkElement>('link[rel="manifest"]')!.href
    return (await fetch(href)).json()
  })
  expect(manifest.display).toBe('standalone')
  expect(manifest.icons.map((i:{sizes:string})=>i.sizes)).toContain('192x192')
  expect(manifest.icons.map((i:{sizes:string})=>i.sizes)).toContain('512x512')
  await page.evaluate(async()=>{await navigator.serviceWorker.ready})
  await page.reload()
  await expect.poll(()=>page.evaluate(()=>Boolean(navigator.serviceWorker.controller))).toBeTruthy()
  const urls = await page.evaluate(async()=>{
    const entries = await Promise.all((await caches.keys()).map(async name=>(await (await caches.open(name)).keys()).map(r=>r.url)))
    return entries.flat()
  })
  expect(urls.some(u=>u.includes('/assets/'))).toBeTruthy()
  expect(urls.some(u=>u.includes('/api/'))).toBeFalsy()
  await page.context().setOffline(true)
  await page.reload()
  await expect(page.getByRole('heading',{name:'SQL verstehen. Selbstständig anwenden.'})).toBeVisible()
  await expect(page.getByText(/Es werden keine Versuche automatisch nachgesendet/)).toBeVisible()
  await expect(page.getByRole('button',{name:'Lernen starten →'})).toBeDisabled()
})
