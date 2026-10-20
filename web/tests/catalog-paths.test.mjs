import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import test from 'node:test'
import { resolveCatalogRoot } from '../../.github/extensions/stl-canvas/catalog-paths.mjs'

const engine = fileURLToPath(new URL('../../', import.meta.url))

test('catalog paths default to workspace; an explicit invalid path fails', () => {
  assert.equal(resolveCatalogRoot(engine, {}), resolve(engine))
  assert.throws(() => resolveCatalogRoot(engine, { CATALOG_ROOT: 'missing-catalog' }), /CATALOG_ROOT/)
})

test('web sync copies external models, metadata and all project image sidecars', () => {
  const root = mkdtempSync(join(tmpdir(), 'catalog-sync-'))
  const sandbox = join(root, 'engine')
  const catalog = join(root, 'catalog')
  try {
    mkdirSync(join(sandbox, 'web', 'scripts'), { recursive: true })
    mkdirSync(join(sandbox, '.github', 'extensions', 'stl-canvas'), { recursive: true })
    for (const relative of [
      'web/scripts/sync-models.mjs',
      '.github/extensions/stl-canvas/catalog-paths.mjs',
    ]) writeFileSync(join(sandbox, relative), readFileSync(join(engine, relative)))
    mkdirSync(join(catalog, 'models'), { recursive: true })
    mkdirSync(join(catalog, 'docs', 'images'), { recursive: true })
    writeFileSync(join(catalog, 'models', 'part.3mf'), 'exact project bytes')
    writeFileSync(join(catalog, 'catalog.json'), JSON.stringify({
      repository: 'harrybin/3d-printing-models',
      models: [{ slug: 'part', outputs: ['models/part.3mf'] }],
    }))
    for (const name of ['part-preview.png', 'part-plate-1-supports.png']) {
      writeFileSync(join(catalog, 'docs', 'images', name), name)
    }
    const result = spawnSync(process.execPath, [join(sandbox, 'web', 'scripts', 'sync-models.mjs')], {
      env: { ...process.env, CATALOG_ROOT: catalog }, encoding: 'utf8',
    })
    assert.equal(result.status, 0, result.stderr)
    const publicDir = join(sandbox, 'web', 'public')
    assert.equal(readFileSync(join(publicDir, 'models', 'part.3mf'), 'utf8'), 'exact project bytes')
    assert.deepEqual(JSON.parse(readFileSync(join(publicDir, 'models', 'models.json'))).files, ['part.3mf'])
    assert.equal(JSON.parse(readFileSync(join(publicDir, 'app-config.json'))).repository.repo, '3d-printing-models')
    for (const name of ['part-preview.png', 'part-plate-1-supports.png']) {
      assert.equal(readFileSync(join(publicDir, 'docs', 'images', name), 'utf8'), name)
    }
  } finally {
    rmSync(root, { recursive: true, force: true })
  }
})
