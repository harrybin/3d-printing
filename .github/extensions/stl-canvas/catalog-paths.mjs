import { existsSync, statSync } from 'node:fs'
import { resolve } from 'node:path'

export function resolveCatalogRoot(workspace = process.cwd(), environment = process.env) {
  const root = resolve(workspace, environment.CATALOG_ROOT || '.')
  if (environment.CATALOG_ROOT && (
    !existsSync(resolve(root, 'models')) || !statSync(resolve(root, 'models')).isDirectory()
  )) {
    throw new Error(`CATALOG_ROOT does not contain a models directory: ${root}`)
  }
  return root
}
