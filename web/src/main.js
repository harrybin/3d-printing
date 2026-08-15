import './style.css'
import * as THREE from 'three'

const app = document.querySelector('#app')
app.innerHTML = `
  <div class="wrap">
    <header>
      <strong>STL Canvas (GitHub Pages)</strong>
      <label>Model:
        <select id="modelSelect"></select>
      </label>
      <button id="reloadBtn">Reload</button>
    </header>
    <main><canvas id="view"></canvas></main>
    <footer id="meta">Lade Modelle …</footer>
  </div>
`

const modelSelect = document.getElementById('modelSelect')
const reloadBtn = document.getElementById('reloadBtn')
const meta = document.getElementById('meta')
const canvas = document.getElementById('view')

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true })
renderer.setPixelRatio(window.devicePixelRatio || 1)
renderer.setSize(canvas.clientWidth, canvas.clientHeight, false)

const scene = new THREE.Scene()
scene.background = new THREE.Color(0x0d1117)

const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 5000)
camera.position.set(180, 180, 180)
camera.lookAt(0, 0, 0)

const ambient = new THREE.AmbientLight(0xffffff, 0.5)
scene.add(ambient)
const dir = new THREE.DirectionalLight(0xffffff, 0.9)
dir.position.set(120, 160, 100)
scene.add(dir)

const grid = new THREE.GridHelper(260, 26, 0x4b5563, 0x374151)
scene.add(grid)

let mesh = null

function parseSTL(buffer) {
  const dv = new DataView(buffer)
  const isAscii = (() => {
    const bytes = new Uint8Array(buffer, 0, Math.min(buffer.byteLength, 256))
    const text = new TextDecoder().decode(bytes).trimStart()
    return /^solid\b/i.test(text)
  })()

  const positions = []

  if (isAscii) {
    const text = new TextDecoder().decode(new Uint8Array(buffer))
    const re = /vertex\s+([-\d.eE+]+)\s+([-\d.eE+]+)\s+([-\d.eE+]+)/g
    let m
    while ((m = re.exec(text)) !== null) {
      positions.push(Number(m[1]), Number(m[2]), Number(m[3]))
    }
  } else {
    if (buffer.byteLength < 84) return null
    const facets = dv.getUint32(80, true)
    let off = 84
    for (let i = 0; i < facets; i++) {
      off += 12 // skip normal
      for (let v = 0; v < 3; v++) {
        positions.push(dv.getFloat32(off, true), dv.getFloat32(off + 4, true), dv.getFloat32(off + 8, true))
        off += 12
      }
      off += 2
      if (off > buffer.byteLength) break
    }
  }

  if (!positions.length) return null
  const g = new THREE.BufferGeometry()
  g.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3))
  g.computeVertexNormals()
  return g
}

async function listModels() {
  const res = await fetch('./models/models.json', { cache: 'no-store' })
  if (!res.ok) throw new Error('models.json nicht gefunden')
  const data = await res.json()
  return Array.isArray(data.files) ? data.files : []
}

async function loadModel(name) {
  meta.textContent = `Lade ${name} …`
  const res = await fetch(`./models/${encodeURIComponent(name)}`)
  if (!res.ok) throw new Error(`Konnte ${name} nicht laden`)
  const buf = await res.arrayBuffer()
  const geom = parseSTL(buf)
  if (!geom) throw new Error('Ungültige STL-Daten')

  if (mesh) {
    scene.remove(mesh)
    mesh.geometry.dispose()
    mesh.material.dispose()
  }

  geom.computeBoundingBox()
  const box = geom.boundingBox
  const center = new THREE.Vector3()
  box.getCenter(center)
  geom.translate(-center.x, -center.y, -box.min.z)

  const mat = new THREE.MeshStandardMaterial({ color: 0xd6d9de, metalness: 0.1, roughness: 0.7 })
  mesh = new THREE.Mesh(geom, mat)
  scene.add(mesh)

  const size = new THREE.Vector3()
  geom.computeBoundingBox()
  geom.boundingBox.getSize(size)
  meta.textContent = `${name} · ${size.x.toFixed(1)} x ${size.y.toFixed(1)} x ${size.z.toFixed(1)} mm`
}

function onResize() {
  const w = canvas.clientWidth || window.innerWidth
  const h = canvas.clientHeight || (window.innerHeight - 90)
  renderer.setSize(w, h, false)
  camera.aspect = w / h
  camera.updateProjectionMatrix()
}

function animate() {
  requestAnimationFrame(animate)
  if (mesh) mesh.rotation.z += 0.002
  renderer.render(scene, camera)
}

window.addEventListener('resize', onResize)

(async () => {
  try {
    const files = await listModels()
    if (!files.length) {
      meta.textContent = 'Keine STL-Dateien unter web/public/models gefunden.'
      return
    }

    modelSelect.innerHTML = files.map((f) => `<option value="${f}">${f}</option>`).join('')
    await loadModel(files[0])

    modelSelect.addEventListener('change', () => loadModel(modelSelect.value).catch((e) => { meta.textContent = String(e) }))
    reloadBtn.addEventListener('click', () => loadModel(modelSelect.value).catch((e) => { meta.textContent = String(e) }))
  } catch (e) {
    meta.textContent = String(e)
  }

  onResize()
  animate()
})()
