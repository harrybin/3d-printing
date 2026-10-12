import test from 'node:test'
import assert from 'node:assert/strict'

import {
  APP_HTML,
  createOrcaLaunchRequest,
  createOrcaSlicerOpenUrl,
  formatPrintMetadataSummary,
  layoutPlateOverview,
  selectDefaultPlate,
} from '../../.github/extensions/stl-canvas/viewer-app.mjs'

test('keeps advanced controls and metadata in collapsible surfaces', () => {
  assert.match(APP_HTML, /<details class="tool-drawer">/)
  assert.match(APP_HTML, /View &amp; model controls/)
  assert.match(APP_HTML, /<details id="metaPanel" class="meta-panel" open>/)
  assert.match(APP_HTML, /<div id="meta">Loading model…<\/div>/)
  assert.doesNotMatch(APP_HTML, /<div class="toolbar secondary">/)
})

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
      supportFilamentGrams: '12.40',
      materialType: 'PLA',
    }),
    {
      visible: true,
      printTime: '19 h 9 min',
      materialUsage: '458.16 g PLA',
      supportUsage: '12.40 g',
      filamentLength: '153614.51 mm',
      status: 'verified',
    },
  )
})

test('reports no support material when the slice needed none', () => {
  const summary = formatPrintMetadataSummary({
    status: 'verified',
    estimatedPrintTimeSeconds: '3600',
    filamentUsageGrams: '20.00',
    supportFilamentGrams: '0.00',
  })
  assert.equal(summary.supportUsage, 'none')
  assert.equal(
    formatPrintMetadataSummary({ status: 'not-verified' }).supportUsage,
    'none',
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

const plates = [{ id: '1' }, { id: '2' }]

test('defaults to all plates on initial load and every file change', () => {
  assert.equal(selectDefaultPlate('new.3mf', '', '1', plates), 'all')
  assert.equal(selectDefaultPlate('new.3mf', 'old.3mf', '2', plates), 'all')
  assert.equal(selectDefaultPlate('new.3mf', 'old.3mf', 'all', plates), 'all')
})

test('same-file reload preserves a valid selection but not a removed plate', () => {
  assert.equal(selectDefaultPlate('same.3mf', 'same.3mf', '2', plates), '2')
  assert.equal(selectDefaultPlate('same.3mf', 'same.3mf', 'all', plates), 'all')
  assert.equal(selectDefaultPlate('same.3mf', 'same.3mf', '3', plates), 'all')
})

test('single-plate files and STL keep the all-geometry selection', () => {
  assert.equal(selectDefaultPlate('single.3mf', 'single.3mf', '1', [plates[0]]), 'all')
  assert.equal(selectDefaultPlate('part.stl', 'part.stl', '2', []), 'all')
  const single = [makePlate('1')]
  assert.equal(layoutPlateOverview(single), single)
  assert.deepEqual(layoutPlateOverview([]), [])
})

function makePlate(id, x = 0, y = 0, width = 100) {
  return {
    id,
    triangles: [[[x, y, 3], [x + width, y, 3], [x, y + 100, 10]]],
    triangleColors: ['#202124'],
    stats: { facets: 1, vertices: 3, uniqueVertices: 3, format: '3mf' },
  }
}

test('preserves baked Orca row/grid offsets and all component transforms', () => {
  const row = [makePlate('1'), makePlate('2', 300)]
  const grid = [...row, makePlate('3', 0, -300), makePlate('4', 300, -300)]
  assert.equal(layoutPlateOverview(row), row)
  assert.equal(layoutPlateOverview(grid), grid)
  assert.deepEqual(row[1].triangles[0][0], [300, 0, 3])
})

test('lays overlapping plates side by side without mutating individual plates', () => {
  const input = [makePlate('1'), makePlate('2', 10, 20), makePlate('3', 0, 0, 400)]
  const before = structuredClone(input)
  const overview = layoutPlateOverview(input)
  assert.deepEqual(input, before)
  assert.deepEqual(overview[0].triangles, input[0].triangles)
  assert.deepEqual(overview[1].triangles[0], [[300, 0, 3], [400, 0, 3], [300, 100, 10]])
  assert.deepEqual(overview[2].triangles[0], [[525, 0, 3], [925, 0, 3], [525, 100, 10]])
  assert.equal(overview[1].triangleColors, input[1].triangleColors)
  assert.equal(overview[2].stats.facets, 1)
  assert.deepEqual(overview[2].stats.bounds.size, { x: 400, y: 100, z: 7 })
})

test('all-plates summary retains whole-project totals and exposes plate count', () => {
  const metadata = {
    status: 'verified',
    estimatedPrintTimeSeconds: '88554',
    filamentUsageGrams: '521.72',
    supportFilamentGrams: '55.09',
    filamentUsageMillimeters: '174923.38',
    materialType: 'PLA',
    plateCount: '2',
  }
  assert.deepEqual(formatPrintMetadataSummary(metadata), {
    visible: true,
    printTime: '24 h 36 min',
    materialUsage: '521.72 g PLA',
    supportUsage: '55.09 g',
    filamentLength: '174923.38 mm',
    status: 'verified',
  })
  assert.match(APP_HTML, /value="all">All plates<\/option>/)
  assert.match(APP_HTML, /id="summaryPlates"/)
})
