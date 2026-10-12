import { cpSync, existsSync, mkdirSync, readdirSync, rmSync, writeFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const webDir = resolve(here, '..')
const repoDir = resolve(webDir, '..')
const sourceDir = join(repoDir, 'models')
const targetDir = join(webDir, 'public', 'models')
const imageSourceDir = join(repoDir, 'docs', 'images')
const imageTargetDir = join(webDir, 'public', 'docs', 'images')
const MODEL_EXTENSIONS = ['.stl', '.3mf']
const PROJECT_IMAGE_PATTERN = /-(?:preview|plate-\d+-supports)\.png$/i

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
writeFileSync(join(targetDir, 'models.json'), JSON.stringify({ files }, null, 2) + '\n', 'utf8')

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
