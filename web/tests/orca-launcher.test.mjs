import test from 'node:test'
import assert from 'node:assert/strict'

import {
  findOrcaSlicer,
  launchOrcaSlicer,
  validateOrcaModelPath,
} from '../../.github/extensions/stl-canvas/orca-launcher.mjs'

test('finds OrcaSlicer from Windows environment paths', () => {
  const expected = String.raw`C:\Apps\OrcaSlicer\orca-slicer.exe`
  assert.equal(findOrcaSlicer({
    platform: 'win32',
    env: { ORCA_SLICER_BIN: expected },
    exists: (candidate) => candidate === expected,
  }), expected)
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

test('launches OrcaSlicer with the exact model path as one argument', async () => {
  const executable = String.raw`C:\Program Files\OrcaSlicer\orca-slicer.exe`
  const modelPath = String.raw`D:\Print Projects\Ghoul's Grip\black plate.3mf`
  let spawnCall
  const child = {
    once(event, handler) {
      if (event === 'spawn') queueMicrotask(handler)
      return this
    },
    unref() {},
  }

  const result = await launchOrcaSlicer(modelPath, {
    findExecutable: () => executable,
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
