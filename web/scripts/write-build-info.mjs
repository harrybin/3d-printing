import { execSync } from 'node:child_process'
import { mkdirSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'

function readGit(command, fallback) {
  try {
    return execSync(command, { encoding: 'utf8' }).trim() || fallback
  } catch {
    return fallback
  }
}

const workflowRef = process.env.PAGES_WORKFLOW_REF || readGit('git branch --show-current', 'main')
const commit = readGit('git rev-parse HEAD', '')
const outputDir = resolve('public')

mkdirSync(outputDir, { recursive: true })
writeFileSync(
  resolve(outputDir, 'build-info.json'),
  JSON.stringify({ workflowRef, commit }, null, 2) + '\n',
  'utf8',
)
