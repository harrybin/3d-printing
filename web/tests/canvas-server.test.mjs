import test from 'node:test'
import assert from 'node:assert/strict'
import { createServer } from 'node:http'

import {
  createModelApiPayload,
  handleOrcaOpenRequest,
} from '../../.github/extensions/stl-canvas/canvas-server-helpers.mjs'

test('model API payload preserves project print metadata for the canvas', () => {
  const payload = createModelApiPayload({
    requested: 'ghouls-grip-print-black-pla.3mf',
    resolved: String.raw`D:\models\ghouls-grip-print-black-pla.3mf`,
    parsed: {
      format: '3mf',
      facets: 12,
      triangles: [[[0, 0, 0], [1, 0, 0], [0, 1, 0]]],
      triangleColors: ['#202124'],
      plates: [],
      projectMetadata: {
        estimatedPrintTimeSeconds: '68960',
        filamentUsageGrams: '458.16',
      },
    },
    content: '',
    mtime: '123:456',
  })

  assert.deepEqual(payload.projectMetadata, {
    estimatedPrintTimeSeconds: '68960',
    filamentUsageGrams: '458.16',
  })
  assert.equal(payload.modelPath, String.raw`D:\models\ghouls-grip-print-black-pla.3mf`)
})

test('model API keeps every plate with its baked grid transforms and project totals', () => {
  const plates = [
    { id: '1', triangles: [[[0, 0, 0], [100, 0, 0], [0, 100, 0]]], triangleColors: ['#202124'] },
    { id: '2', triangles: [[[300, 0, 0], [400, 0, 0], [300, 100, 0]]], triangleColors: ['#202124'] },
  ]
  const projectMetadata = {
    plateCount: '2',
    estimatedPrintTimeSeconds: '49988',
    filamentUsageGrams: '330.96',
    supportFilamentGrams: '17.98',
    filamentUsageMillimeters: '110966.48',
  }
  const payload = createModelApiPayload({
    requested: 'project.3mf',
    resolved: String.raw`D:\models\project.3mf`,
    parsed: {
      format: '3mf',
      triangles: plates.flatMap((plate) => plate.triangles),
      triangleColors: plates.flatMap((plate) => plate.triangleColors),
      plates,
      projectMetadata,
    },
    mtime: '123:456',
  })
  assert.equal(payload.plates, plates)
  assert.equal(payload.projectMetadata, projectMetadata)
  assert.equal(payload.triangles.length, 2)
  assert.equal(payload.stats.plates, undefined)
})

test('Orca endpoint accepts JSON and launches the exact current model path', async (t) => {
  const expectedPath = String.raw`D:\Print Projects\Ghoul's Grip\black plate.3mf`
  let launchedPath = ''
  const server = createServer((req, res) => handleOrcaOpenRequest(req, res, {
    defaultModelPath: String.raw`D:\models\fallback.3mf`,
    expectedNonce: 'server-nonce',
    validate: (modelPath) => modelPath,
    launch: async (modelPath) => {
      launchedPath = modelPath
      return String.raw`C:\Program Files\OrcaSlicer\orca-slicer.exe`
    },
  }))
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve))
  t.after(() => new Promise((resolve) => server.close(resolve)))
  const { port } = server.address()

  const response = await fetch(`http://127.0.0.1:${port}/api/open-in-orca`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ modelPath: expectedPath, nonce: 'server-nonce' }),
  })

  assert.equal(response.status, 200)
  assert.equal(launchedPath, expectedPath)
  assert.deepEqual(await response.json(), {
    ok: true,
    executable: String.raw`C:\Program Files\OrcaSlicer\orca-slicer.exe`,
    file: expectedPath,
  })
})

test('Orca endpoint rejects a nonce mismatch before validation or launch', async (t) => {
  let validationCalls = 0
  let launchCalls = 0
  const server = createServer((req, res) => handleOrcaOpenRequest(req, res, {
    defaultModelPath: String.raw`D:\models\fallback.3mf`,
    expectedNonce: 'server-nonce',
    validate: () => {
      validationCalls += 1
      return ''
    },
    launch: async () => {
      launchCalls += 1
      return ''
    },
  }))
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve))
  t.after(() => new Promise((resolve) => server.close(resolve)))
  const { port } = server.address()

  const response = await fetch(`http://127.0.0.1:${port}/api/open-in-orca`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      modelPath: String.raw`D:\models\fallback.3mf`,
      nonce: 'wrong-nonce',
    }),
  })

  assert.equal(response.status, 403)
  assert.equal(validationCalls, 0)
  assert.equal(launchCalls, 0)
  assert.deepEqual(await response.json(), {
    ok: false,
    error: 'Forbidden',
  })
})
