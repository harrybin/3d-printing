import test from 'node:test'
import assert from 'node:assert/strict'

import {
  defaultOpenCommand,
  launchDefault3mfApp,
  validateOrcaModelPath,
} from '../../.github/extensions/stl-canvas/orca-launcher.mjs'

test('resolves the OS default-application opener per platform', () => {
  const file = String.raw`D:\repo\models\part.3mf`
  assert.deepEqual(
    defaultOpenCommand(file, { platform: 'win32', env: { SystemRoot: String.raw`C:\Windows` } }),
    { command: String.raw`C:\Windows\explorer.exe`, args: [file] },
  )
  assert.deepEqual(defaultOpenCommand('/m/p.3mf', { platform: 'darwin', env: {} }), { command: 'open', args: ['/m/p.3mf'] })
  assert.deepEqual(defaultOpenCommand('/m/p.3mf', { platform: 'linux', env: {} }), { command: 'xdg-open', args: ['/m/p.3mf'] })
})

test('rejects a missing or non-3MF OrcaSlicer model path', () => {
  const workspaceRoot = String.raw`D:\repo`
  const dependencies = { exists: () => true, canonicalize: (value) => value }
  assert.throws(
    () => validateOrcaModelPath(String.raw`D:\repo\models\part.stl`, workspaceRoot, dependencies),
    /Only 3MF projects/,
  )
  assert.throws(
    () => validateOrcaModelPath(
      String.raw`D:\repo\models\missing.3mf`,
      workspaceRoot,
      { ...dependencies, exists: () => false },
    ),
    /Model file not found/,
  )
})

test('rejects existing 3MF paths outside the current workspace', () => {
  assert.throws(
    () => validateOrcaModelPath(
      String.raw`D:\outside\attacker.3mf`,
      String.raw`D:\repo`,
      { exists: () => true, canonicalize: (value) => value },
    ),
    /outside the current workspace/,
  )
})

test('preserves the exact canonical path for a 3MF inside the workspace', () => {
  const modelPath = String.raw`D:\repo\models\Ghoul's Grip\black plate.3mf`
  assert.equal(
    validateOrcaModelPath(
      modelPath,
      String.raw`D:\repo`,
      { exists: () => true, canonicalize: (value) => value },
    ),
    modelPath,
  )
})

test('launches the default 3MF application with the exact model path as one argument', async () => {
  const executable = String.raw`C:\Windows\explorer.exe`
  const modelPath = String.raw`D:\Print Projects\Ghoul's Grip\black plate.3mf`
  let spawnCall
  const child = {
    once(event, handler) {
      if (event === 'spawn') queueMicrotask(handler)
      return this
    },
    unref() {},
  }

  const result = await launchDefault3mfApp(modelPath, {
    resolveCommand: (file) => ({ command: executable, args: [file] }),
    spawnProcess(command, args, options) {
      spawnCall = { command, args, options }
      return child
    },
  })

  assert.equal(result, executable)
  assert.deepEqual(spawnCall.command, executable)
  assert.deepEqual(spawnCall.args, [modelPath])
  assert.equal(spawnCall.options.windowsHide, false)
})
