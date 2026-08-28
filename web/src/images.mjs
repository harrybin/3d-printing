const THUMBNAIL_SIZE = 240

async function decodeImage(blob) {
  if (typeof createImageBitmap === 'function') {
    try {
      return await createImageBitmap(blob)
    } catch {
      // Fall through to the HTMLImageElement path below.
    }
  }
  const url = URL.createObjectURL(blob)
  try {
    return await new Promise((resolve, reject) => {
      const image = new Image()
      image.onload = () => resolve(image)
      image.onerror = () => reject(new Error('Bild konnte nicht gelesen werden.'))
      image.src = url
    })
  } finally {
    URL.revokeObjectURL(url)
  }
}

function imageSize(source) {
  return {
    width: source.width || source.naturalWidth || 0,
    height: source.height || source.naturalHeight || 0,
  }
}

function canvasToBlob(canvas, type, quality) {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => (blob ? resolve(blob) : reject(new Error('Canvas konnte nicht exportiert werden.'))),
      type,
      quality,
    )
  })
}

export async function describeImage(blob) {
  const source = await decodeImage(blob)
  const { width, height } = imageSize(source)
  const scale = Math.min(1, THUMBNAIL_SIZE / Math.max(width || 1, height || 1))
  const canvas = document.createElement('canvas')
  canvas.width = Math.max(1, Math.round(width * scale))
  canvas.height = Math.max(1, Math.round(height * scale))
  const context = canvas.getContext('2d')
  context.drawImage(source, 0, 0, canvas.width, canvas.height)
  source.close?.()
  return {
    width,
    height,
    thumbnail: await canvasToBlob(canvas, 'image/jpeg', 0.72),
  }
}

/**
 * Client-side port of scripts/make_contact_sheet.py: renders every reference
 * image into a numbered grid so the user can cite tile numbers in the prompt.
 */
export async function buildContactSheet(records, { tile = 320, columns = 0, label = 'Referenzbilder' } = {}) {
  if (!records.length) throw new Error('Keine Bilder vorhanden.')
  const cols = columns || Math.min(4, Math.ceil(Math.sqrt(records.length)))
  const rows = Math.ceil(records.length / cols)
  const captionHeight = 34
  const headerHeight = 46
  const padding = 12
  const cellWidth = tile + padding
  const cellHeight = tile + captionHeight + padding

  const canvas = document.createElement('canvas')
  canvas.width = cols * cellWidth + padding
  canvas.height = headerHeight + rows * cellHeight + padding
  const context = canvas.getContext('2d')
  context.fillStyle = '#0f1720'
  context.fillRect(0, 0, canvas.width, canvas.height)
  context.fillStyle = '#e6edf3'
  context.font = '600 20px system-ui, sans-serif'
  context.textBaseline = 'top'
  context.fillText(`${label} · ${records.length} Bild(er)`, padding, padding)

  for (const [index, record] of records.entries()) {
    const column = index % cols
    const row = Math.floor(index / cols)
    const x = padding + column * cellWidth
    const y = headerHeight + row * cellHeight

    context.fillStyle = '#161b22'
    context.fillRect(x, y, tile, tile)

    try {
      const source = await decodeImage(record.blob)
      const { width, height } = imageSize(source)
      const scale = Math.min(tile / (width || 1), tile / (height || 1))
      const drawWidth = Math.max(1, Math.round(width * scale))
      const drawHeight = Math.max(1, Math.round(height * scale))
      context.drawImage(
        source,
        x + Math.round((tile - drawWidth) / 2),
        y + Math.round((tile - drawHeight) / 2),
        drawWidth,
        drawHeight,
      )
      source.close?.()
    } catch {
      context.fillStyle = '#f85149'
      context.font = '14px system-ui, sans-serif'
      context.fillText('nicht lesbar', x + 10, y + 10)
    }

    context.fillStyle = '#1f6feb'
    context.fillRect(x, y, 40, 26)
    context.fillStyle = '#ffffff'
    context.font = '700 16px system-ui, sans-serif'
    context.fillText(String(index + 1).padStart(2, '0'), x + 8, y + 5)

    context.fillStyle = '#8b949e'
    context.font = '13px system-ui, sans-serif'
    const caption = `${record.displayName} · ${record.width}×${record.height}`
    context.fillText(caption.length > 42 ? `${caption.slice(0, 41)}…` : caption, x, y + tile + 6)
  }

  return canvasToBlob(canvas, 'image/png')
}

export function buildImageContextBlock(records) {
  if (!records.length) return ''
  const lines = records.map((record, index) => {
    const tile = String(index + 1).padStart(2, '0')
    const note = record.note ? ` – ${record.note}` : ''
    return `- Kachel ${tile}: ${record.displayName} (${record.width}×${record.height} px)${note}`
  })
  return [
    'Referenzbilder (liegen nur im Browser des Benutzers, du kannst sie nicht öffnen):',
    ...lines,
    'Alle maßgeblichen Maße stehen im Text oben. Wenn eine Angabe fehlt, arbeite mit einer klar als Schätzung markierten Annahme.',
  ].join('\n')
}
