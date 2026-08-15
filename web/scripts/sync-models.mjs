import { cpSync, existsSync, mkdirSync, readdirSync, rmSync, writeFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const webDir = resolve(here, '..')
const repoDir = resolve(webDir, '..')
const sourceDir = join(repoDir, 'models')
const targetDir = join(webDir, 'public', 'models')

mkdirSync(targetDir, { recursive: true })
for (const name of readdirSync(targetDir)) {
  if (name.toLowerCase().endsWith('.stl')) rmSync(join(targetDir, name), { force: true })
}

const files = existsSync(sourceDir)
  ? readdirSync(sourceDir).filter((name) => name.toLowerCase().endsWith('.stl')).sort((a, b) => a.localeCompare(b))
  : []

for (const name of files) cpSync(join(sourceDir, name), join(targetDir, name))
writeFileSync(join(targetDir, 'models.json'), JSON.stringify({ files }, null, 2) + '\n', 'utf8')
