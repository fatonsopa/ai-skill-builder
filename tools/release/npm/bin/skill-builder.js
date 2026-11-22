#!/usr/bin/env node
// npm entry for Skill Builder: prepares the payload's Python environment once,
// then runs the same release command as the GitHub installer.
'use strict';
const { spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const payload = path.join(__dirname, '..', 'payload');
const venv = path.join(payload, '.venv');
const venvPython = path.join(venv, 'bin', 'python');

function fail(message) {
  process.stderr.write(`skill-builder: ${message}\n`);
  process.exit(1);
}

function findPython() {
  for (const name of ['python3.14', 'python3.13', 'python3.12', 'python3.11', 'python3']) {
    const check = spawnSync(name, ['-c', 'import sys; sys.exit(sys.version_info < (3, 11))'], { stdio: 'ignore' });
    if (check.status === 0) return name;
  }
  return null;
}

if (process.platform === 'win32') fail('native Windows is not supported; use macOS, Linux or WSL.');
if (!fs.existsSync(venvPython)) {
  const python = findPython();
  if (!python) fail('Python 3.11 or later is required. Install it, make sure python3.11 or newer is on PATH, then run skill-builder again.');
  const staging = `${venv}.staging-${process.pid}`;
  const steps = [[python, ['-m', 'venv', staging]],
    [path.join(staging, 'bin', 'python'), ['-m', 'pip', 'install', '--quiet', '--disable-pip-version-check', '-r', path.join(payload, 'scripts', 'requirements-lock.txt')]]];
  for (const [command, args] of steps) {
    if (spawnSync(command, args, { stdio: ['ignore', 'ignore', 'inherit'] }).status !== 0) {
      fs.rmSync(staging, { recursive: true, force: true });
      fail(`could not set up the Python environment in ${venv}. Fix the error above, then run skill-builder again.`);
    }
  }
  fs.renameSync(staging, venv);
}
const result = spawnSync(venvPython, [path.join(payload, 'scripts', 'release_cli.py'), ...process.argv.slice(2)],
  { stdio: 'inherit', env: { ...process.env, SKILL_BUILDER_LAUNCHER: process.argv[1] } });
process.exit(result.status === null ? 1 : result.status);
