import test from 'node:test'
import assert from 'node:assert/strict'

import {
  createOrcaLaunchRequest,
  createOrcaSlicerOpenUrl,
  formatPrintMetadataSummary,
} from '../../.github/extensions/stl-canvas/viewer-app.mjs'

test('builds the official OrcaSlicer open URL for a current 3MF file', () => {
  assert.equal(
    createOrcaSlicerOpenUrl(
      'project.3mf',
      './models/project.3mf',
      'https://example.test/viewer/',
    ),
    'orcaslicer://open/?file=https%3A%2F%2Fexample.test%2Fviewer%2Fmodels%2Fproject.3mf',
  )
})

test('percent-encodes the complete nested URL for OrcaSlicer to decode once', () => {
  assert.equal(
    createOrcaSlicerOpenUrl(
      'Project Copy.3MF',
      './models/Project Copy.3MF?download=1&return=%2Fmodels%2Fnext%3Fa%3D1%26b%3D2',
      'https://example.test/',
    ),
    'orcaslicer://open/?file=https%3A%2F%2Fexample.test%2Fmodels%2FProject%2520Copy.3MF%3Fdownload%3D1%26return%3D%252Fmodels%252Fnext%253Fa%253D1%2526b%253D2',
  )
})

test('does not expose the action for non-3MF or unsafe URLs', () => {
  assert.equal(createOrcaSlicerOpenUrl('part.stl', 'https://example.test/part.stl', 'https://example.test/'), '')
  assert.equal(createOrcaSlicerOpenUrl('part.3mf', 'javascript:alert(1)', 'https://example.test/'), '')
  assert.equal(createOrcaSlicerOpenUrl('part.3mf', 'https://user:secret@example.test/part.3mf', 'https://example.test/'), '')
})

test('formats verified print time and material usage for the visible summary', () => {
  assert.deepEqual(
    formatPrintMetadataSummary({
      status: 'verified',
      estimatedPrintTimeSeconds: '68960',
      filamentUsageGrams: '458.16',
      filamentUsageMillimeters: '153614.51',
      materialType: 'PLA',
    }),
    {
      visible: true,
      printTime: '19 h 9 min',
      materialUsage: '458.16 g PLA',
      filamentLength: '153614.51 mm',
      status: 'verified',
    },
  )
})

test('posts the exact Windows model path to the local OrcaSlicer endpoint', () => {
  const modelPath = String.raw`D:\Print Projects\Ghoul's Grip\black plate.3mf`
  assert.deepEqual(createOrcaLaunchRequest('/api/open-in-orca', modelPath, 'server-nonce'), {
    url: '/api/open-in-orca',
    options: {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ modelPath, nonce: 'server-nonce' }),
    },
  })
})
