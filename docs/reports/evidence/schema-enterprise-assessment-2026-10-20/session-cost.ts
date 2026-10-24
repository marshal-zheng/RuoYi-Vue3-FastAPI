import { performance } from 'node:perf_hooks'
import { createSession } from '/Users/hqz/Downloads/element-plus/packages/schema-form/src/session.ts'
const results = []
for (const rows of [50, 200, 1000]) {
  const values = { title: 'Order', rows: Array.from({length: rows}, (_, i) => ({ id: `row-${i}`, name: `Item ${i}`, qty: 1, unit: 'kg', price: 10.5, remark: 'x'.repeat(100) })) }
  const session = createSession(values, async () => ({ok: true}))
  const ms: number[] = []
  for (let i = 0; i < 60; i++) {
    values.rows[rows - 1].remark = `edit-${i}` + 'x'.repeat(100)
    const start = performance.now()
    session.observe(values)
    void session.dirty.value
    const elapsed = performance.now() - start
    if(i >= 10) ms.push(elapsed)
  }
  ms.sort((a,b)=>a-b)
  results.push({rows,bytes:Buffer.byteLength(JSON.stringify(values)),samples:ms.length,p50ms:Number(ms[Math.floor(ms.length*.5)].toFixed(3)),p95ms:Number(ms[Math.floor(ms.length*.95)].toFixed(3))})
  session.dispose()
}
console.log(JSON.stringify({kind:'session.observe plus dirty only; no FormCreate, Vue DOM, browser or network',node:process.version,results},null,2))
