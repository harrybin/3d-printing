import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { resolveCatalogRoot } from '../../.github/extensions/stl-canvas/catalog-paths.mjs'

const here = dirname(fileURLToPath(import.meta.url))
const webDir = resolve(here, '..')
const repoDir = resolveCatalogRoot(resolve(webDir, '..'))
const sourceDir = join(repoDir, 'models')
const targetDir = join(webDir, 'public', 'models')
const imageSourceDir = join(repoDir, 'docs', 'images')
const imageTargetDir = join(webDir, 'public', 'docs', 'images')
const MODEL_EXTENSIONS = ['.stl', '.3mf']
const PROJECT_IMAGE_PATTERN = /-(?:preview|plate-\d+-supports)\.png$/i

if (!existsSync(sourceDir)) {
  throw new Error('No model catalog. Set CATALOG_ROOT to your 3d-printing-models checkout.')
}
const manifest = JSON.parse(readFileSync(join(repoDir, 'catalog.json'), 'utf8'))
const [owner, repo] = manifest.repository.split('/')
if (!owner || !repo) throw new Error('catalog.json must declare an owner/repository')
const config = {
  app: { title: '3d-printing model viewer', tagline: 'Printable models and their source catalog.' },
  repository: { owner, repo, defaultBranch: 'main', visibility: 'public' },
}

mkdirSync(targetDir, { recursive: true })
for (const name of readdirSync(targetDir)) {
  if (MODEL_EXTENSIONS.some((extension) => name.toLowerCase().endsWith(extension))) {
    rmSync(join(targetDir, name), { force: true })
  }
}

const files = existsSync(sourceDir)
  ? readdirSync(sourceDir)
      .filter((name) => MODEL_EXTENSIONS.some((extension) => name.toLowerCase().endsWith(extension)))
      .sort((a, b) => a.localeCompare(b))
  : []

for (const name of files) cpSync(join(sourceDir, name), join(targetDir, name))
writeFileSync(join(targetDir, 'models.json'), JSON.stringify({ files, models: manifest.models }, null, 2) + '\n', 'utf8')
writeFileSync(join(webDir, 'public', 'app-config.json'), JSON.stringify(config, null, 2) + '\n', 'utf8')

mkdirSync(imageTargetDir, { recursive: true })
for (const name of readdirSync(imageTargetDir)) {
  if (PROJECT_IMAGE_PATTERN.test(name)) rmSync(join(imageTargetDir, name), { force: true })
}
if (existsSync(imageSourceDir)) {
  for (const name of readdirSync(imageSourceDir)) {
    if (PROJECT_IMAGE_PATTERN.test(name)) {
      cpSync(join(imageSourceDir, name), join(imageTargetDir, name))
    }
  }
}
