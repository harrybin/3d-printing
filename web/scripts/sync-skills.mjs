import { readFile, readdir, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(here, '..', '..')
const skillsRoot = path.join(repoRoot, '.github', 'skills')
const outputFile = path.join(repoRoot, 'web', 'public', 'skills-manifest.json')

function parseFrontmatter(text) {
  const match = /^---\r?\n([\s\S]*?)\r?\n---/.exec(text)
  if (!match) return {}
  const fields = {}
  let key = null
  for (const rawLine of match[1].split(/\r?\n/)) {
    const keyed = /^([A-Za-z0-9_-]+):\s*(.*)$/.exec(rawLine)
    if (keyed) {
      key = keyed[1]
      fields[key] = keyed[2]
    } else if (key && rawLine.trim()) {
      fields[key] = `${fields[key]} ${rawLine.trim()}`.trim()
    }
  }
  for (const [name, value] of Object.entries(fields)) {
    fields[name] = value.trim().replace(/^["']|["']$/g, '')
  }
  return fields
}

async function findSkillFile(directory) {
  // Match case-sensitively: the repo mixes SKILL.md and skill.md, and a
  // case-insensitive filesystem would otherwise produce broken GitHub links.
  const entries = await readdir(directory, { withFileTypes: true })
  const match = entries.find((entry) => entry.isFile() && ['SKILL.md', 'skill.md'].includes(entry.name))
  return match ? path.join(directory, match.name) : null
}

async function collectSkills() {
  const entries = await readdir(skillsRoot, { withFileTypes: true })
  const skills = []
  for (const entry of entries) {
    if (!entry.isDirectory()) continue
    const skillFile = await findSkillFile(path.join(skillsRoot, entry.name))
    if (!skillFile) continue
    const text = await readFile(skillFile, 'utf8')
    const frontmatter = parseFrontmatter(text)
    skills.push({
      id: frontmatter.name || entry.name,
      name: frontmatter.name || entry.name,
      description: frontmatter.description || '',
      source: path.relative(repoRoot, skillFile).split(path.sep).join('/'),
    })
  }
  return skills.sort((a, b) => a.id.localeCompare(b.id))
}

const skills = await collectSkills()
const manifest = {
  description:
    'Alle Repository-Skills stehen jedem Copilot-Run automatisch zur Verfügung. Eine Auswahl ist nicht nötig – Copilot entscheidet anhand des Prompts, welche Skills es verwendet.',
  skills,
}

await writeFile(outputFile, `${JSON.stringify(manifest, null, 2)}\n`, 'utf8')
console.log(`skills-manifest.json written with ${skills.length} skill(s).`)
