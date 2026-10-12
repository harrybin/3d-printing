import test from 'node:test'
import assert from 'node:assert/strict'

import {
  APP_HTML,
  createOrcaLaunchRequest,
  createOrcaSlicerOpenUrl,
  formatPrintMetadataSummary,
  plateSupportImagePath,
  projectPreviewImagePath,
  renderPlatePrintDetails,
  layoutPlateOverview,
  orcaMaterialAssignments,
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
    'not available',
  )
})

test('renders per-plate details without substituting project totals', () => {
  const metadata = {
    filamentUsageGrams: '999',
    plateDetails: JSON.stringify([
      { name: 'Plate 1 - Black PLA', estimatedPrintTimeSeconds: '43427',
        filamentUsageGrams: '336.98', supportFilamentGrams: '18.41',
        filamentUsageMillimeters: '112982.82', status: 'not-verified' },
      { name: 'Plate 4', estimatedPrintTimeSeconds: '3492',
        filamentUsageGrams: '9.66', supportFilamentGrams: '0.00',
        filamentUsageMillimeters: '3238.45', status: 'verified' },
    ]),
  }
  const html = renderPlatePrintDetails(metadata)
  assert.match(html, /<details class="plate-print-details">/)
  assert.match(html, /Print data by plate \(2\)/)
  assert.match(html, /336.98 g/)
  assert.match(html, /18.41 g/)
  assert.match(html, /3238.45 mm/)
  assert.match(html, /<td>none<\/td>/)
  assert.doesNotMatch(html, /999/)
})

test('resolves project and per-plate screenshot sidecars from a 3MF filename', () => {
  assert.equal(
    projectPreviewImagePath('models/ghouls-grip-print.3mf'),
    'docs/images/ghouls-grip-print-preview.png',
  )
  assert.equal(
    plateSupportImagePath('ghouls-grip-print.3mf', 5),
    'docs/images/ghouls-grip-print-plate-5-supports.png',
  )
  assert.equal(projectPreviewImagePath('part.stl'), '')
  assert.equal(plateSupportImagePath('part.3mf', 0), '')
  assert.equal(plateSupportImagePath('part.3mf', 'not-a-plate'), '')
})

test('offers support screenshot buttons inside the expandable per-plate details', () => {
  const html = renderPlatePrintDetails({
    plateDetails: JSON.stringify([
      { name: 'Plate 1 - Black PLA', status: 'verified' },
      { name: 'Plate 2 - Bone PLA', status: 'verified' },
    ]),
  }, { file: 'ghouls-grip-print.3mf' })
  assert.match(html, /<details class="plate-print-details">/)
  assert.match(html, /<th scope="col">Support preview<\/th>/)
  assert.match(html, /ghouls-grip-print-plate-1-supports\.png/)
  assert.match(html, /ghouls-grip-print-plate-2-supports\.png/)
})

test('shows per-plate support lengths and the all-plate project-total label', () => {
  const html = renderPlatePrintDetails({
    plateDetails: JSON.stringify([
      { name: 'Black shells', supportFilamentMillimeters: '700' },
      { name: 'Bone parts', supportFilamentMillimeters: 0 },
      { name: 'Unknown', supportFilamentMillimeters: -1 },
    ]),
  }, { file: 'ghouls-grip-print.3mf' })
  assert.match(APP_HTML, /All plates · project total/)
  assert.match(html, /Support length/)
  assert.match(html, /700\.00 mm/)
  assert.match(html, /0\.00 mm/)
  assert.doesNotMatch(html, /-1\.00 mm/)
  assert.equal((html.match(/<details /g) || []).length, 1)
  assert.equal((html.match(/data-project-image=/g) || []).length, 3)
})

test('reports missing or invalid per-plate metadata and escapes plate names', () => {
  assert.equal(renderPlatePrintDetails({}), '')
  assert.match(renderPlatePrintDetails({ status: 'not-verified' }), /not available/)
  assert.match(renderPlatePrintDetails({ plateDetails: '{' }), /invalid plateDetails/)
  assert.match(renderPlatePrintDetails({ plateDetails: '[null]' }), /expected plate records/)
  assert.match(renderPlatePrintDetails({ plateDetails: '[]' }), /No per-plate/)
  const html = renderPlatePrintDetails({ plateDetails: [{ name: '<img onerror="x">' }] })
  assert.match(html, /&lt;img/)
  assert.doesNotMatch(html, /<img/)
  assert.match(html, /not available/)
})

test('rounds print time without producing sixty-minute fields and keeps numeric zero', () => {
  const summary = formatPrintMetadataSummary({
    estimatedPrintTimeSeconds: 3599, filamentUsageGrams: 0,
    filamentUsageMillimeters: 0, supportFilamentGrams: 0,
  })
  assert.equal(summary.printTime, '1 h 0 min')
  assert.equal(summary.materialUsage, '0 g')
  assert.equal(summary.filamentLength, '0 mm')
  assert.equal(summary.supportUsage, 'none')
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
  assert.deepEqual(layoutPlateOverview(grid).map((plate) => plate.triangles), grid.map((plate) => plate.triangles))
  assert.deepEqual(row[1].triangles[0][0], [300, 0, 3])
})

test('lays overlapping plates in a grid without mutating individual plates', () => {
  const input = [makePlate('1'), makePlate('2', 10, 20), makePlate('3', 0, 0, 400)]
  const before = structuredClone(input)
  const overview = layoutPlateOverview(input)
  assert.deepEqual(input, before)
  assert.deepEqual(overview[0].triangles, input[0].triangles)
  assert.deepEqual(overview[1].triangles[0], [[450, 0, 3], [550, 0, 3], [450, 100, 10]])
  assert.deepEqual(overview[2].triangles[0], [[-150, -300, 3], [250, -300, 3], [-150, -200, 10]])
  assert.equal(overview[1].triangleColors, input[1].triangleColors)
  assert.equal(overview[2].stats.facets, 1)
  assert.deepEqual(overview[2].stats.bounds.size, { x: 400, y: 100, z: 7 })
})

test('reflows five or six baked line plates into a three-column grid', () => {
  for (const count of [5, 6]) {
    const input = Array.from({ length: count }, (_, index) => makePlate(String(index + 1), index * 300))
    const before = structuredClone(input)
    const output = layoutPlateOverview(input)
    assert.deepEqual(input, before)
    assert.deepEqual(output.map((plate) => plate.triangles[0][0]), [
      [0, 0, 3], [300, 0, 3], [600, 0, 3],
      [0, -300, 3], [300, -300, 3], ...(count === 6 ? [[600, -300, 3]] : []),
    ])
  }
})

function xmlNode(localName, attributes = {}, children = []) {
  return { localName, children, getAttribute: (name) => attributes[name] ?? null }
}

test('reads Orca one-based filament slots and part overrides, including inherited zero', () => {
  const meta = (value) => xmlNode('metadata', { key: 'extruder', value })
  const doc = { documentElement: xmlNode('config', {}, [
    xmlNode('object', { id: '52' }, [meta('3'), xmlNode('part', { id: '51' }, [meta('0')])]),
    xmlNode('object', { id: '4' }, [meta('1'), xmlNode('part', { id: '3' }, [meta('2')])]),
    xmlNode('object', { id: '8' }, [meta('9')]),
  ]) }
  const assignments = orcaMaterialAssignments(doc, { filament_colour: ['#202124', '#D8C6A5FF', '#F1EBDD'] })
  assert.equal(assignments.get('52').color, '#f1ebdd')
  assert.equal(assignments.get('52').parts.get('51'), '#f1ebdd')
  assert.equal(assignments.get('4').color, '#202124')
  assert.equal(assignments.get('4').parts.get('3'), '#d8c6a5')
  assert.equal(assignments.get('8').color, null)
  assert.equal(orcaMaterialAssignments(doc, {}).get('4').color, null)
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
