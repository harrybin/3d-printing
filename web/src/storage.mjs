const DB_NAME = 'stl-copilot-store'
const DB_VERSION = 1

export const STORE_MODELS = 'models'
export const STORE_IMAGES = 'images'
export const STORE_FILES = 'files'

let dbPromise = null

function openDatabase() {
  if (dbPromise) return dbPromise
  dbPromise = new Promise((resolve, reject) => {
    if (typeof indexedDB === 'undefined') {
      reject(new Error('Dieser Browser unterstützt IndexedDB nicht.'))
      return
    }
    const request = indexedDB.open(DB_NAME, DB_VERSION)
    request.onupgradeneeded = () => {
      const db = request.result
      for (const store of [STORE_MODELS, STORE_IMAGES, STORE_FILES]) {
        if (!db.objectStoreNames.contains(store)) db.createObjectStore(store, { keyPath: 'key' })
      }
    }
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error || new Error('IndexedDB konnte nicht geöffnet werden.'))
  })
  return dbPromise
}

function runTransaction(storeName, mode, work) {
  return openDatabase().then(
    (db) =>
      new Promise((resolve, reject) => {
        const tx = db.transaction(storeName, mode)
        const store = tx.objectStore(storeName)
        let result
        try {
          result = work(store)
        } catch (error) {
          reject(error)
          return
        }
        tx.oncomplete = () => resolve(result)
        tx.onabort = () => reject(tx.error || new Error('IndexedDB-Transaktion abgebrochen.'))
        tx.onerror = () => reject(tx.error || new Error('IndexedDB-Transaktion fehlgeschlagen.'))
      }),
  )
}

function requestValue(request) {
  const holder = { value: undefined }
  request.onsuccess = () => {
    holder.value = request.result
  }
  return holder
}

export async function putRecord(storeName, record) {
  const stored = { ...record, savedAt: record.savedAt || new Date().toISOString() }
  try {
    await runTransaction(storeName, 'readwrite', (store) => store.put(stored))
  } catch (error) {
    if (error && (error.name === 'QuotaExceededError' || String(error.message).includes('quota'))) {
      throw new Error('Der lokale Browser-Speicher ist voll. Bitte gespeicherte Dateien oder Bilder löschen.')
    }
    throw error
  }
  return stored
}

export async function listRecords(storeName) {
  const holder = await runTransaction(storeName, 'readonly', (store) => requestValue(store.getAll()))
  const records = Array.isArray(holder.value) ? holder.value : []
  return records.sort((a, b) => String(b.savedAt).localeCompare(String(a.savedAt)))
}

export async function getRecord(storeName, key) {
  const holder = await runTransaction(storeName, 'readonly', (store) => requestValue(store.get(key)))
  return holder.value || null
}

export async function deleteRecord(storeName, key) {
  await runTransaction(storeName, 'readwrite', (store) => store.delete(key))
}

export async function clearStore(storeName) {
  await runTransaction(storeName, 'readwrite', (store) => store.clear())
}

export function stripBlob(record) {
  if (!record) return record
  const { blob, thumbnail, ...rest } = record
  return { ...rest, hasThumbnail: Boolean(thumbnail) }
}

export async function estimateUsage() {
  if (!navigator.storage?.estimate) return null
  try {
    const { usage, quota } = await navigator.storage.estimate()
    return { usage: usage || 0, quota: quota || 0 }
  } catch {
    return null
  }
}

function decodeBase64(base64) {
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index)
  return bytes
}

/**
 * Moves models saved by the previous localStorage-based build into IndexedDB so
 * users keep the files they already downloaded from earlier workflow runs.
 */
export async function migrateLegacyModels(legacyKey) {
  let raw
  try {
    raw = localStorage.getItem(legacyKey)
  } catch {
    return 0
  }
  if (!raw) return 0
  let entries
  try {
    entries = JSON.parse(raw)
  } catch {
    localStorage.removeItem(legacyKey)
    return 0
  }
  if (!Array.isArray(entries) || !entries.length) {
    localStorage.removeItem(legacyKey)
    return 0
  }
  let migrated = 0
  for (const entry of entries) {
    if (!entry?.key || !entry?.base64) continue
    try {
      await putRecord(STORE_MODELS, {
        key: entry.key,
        displayName: entry.displayName || entry.key,
        blob: new Blob([decodeBase64(entry.base64)], { type: entry.contentType || 'application/octet-stream' }),
        contentType: entry.contentType || 'application/octet-stream',
        size: entry.size || 0,
        savedAt: entry.savedAt || new Date().toISOString(),
        sourceArtifact: entry.sourceArtifact || '',
        runId: entry.runId || '',
        runNumber: entry.runNumber || null,
        userLogin: entry.userLogin || '',
        version: entry.version || String(Date.now()),
        viewerEligible: Boolean(entry.viewerEligible),
      })
      migrated += 1
    } catch {
      // Skip entries that cannot be migrated instead of blocking startup.
    }
  }
  localStorage.removeItem(legacyKey)
  return migrated
}
