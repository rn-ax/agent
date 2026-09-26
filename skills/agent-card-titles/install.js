#!/usr/bin/env node
/**
 * Installer for agent-card-titles.
 *
 *   node install.js              register the hooks
 *   node install.js --recompute  register, then retitle every existing card right away
 *   node install.js --uninstall  remove the hooks (leaves card titles as they are)
 *   node install.js --dry-run    print the resulting settings.json without writing
 *
 * Options:
 *   --home <dir>   operate on a different .claude directory (default: $CLAUDE_CONFIG_DIR
 *                  or ~/.claude). Handy for testing against a scratch copy.
 *   --node <path>  executable to run the hook with (default: the node running this script).
 *
 * Idempotent: re-running never double-registers. settings.json is backed up before write.
 */
'use strict';

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execFileSync } = require('child_process');

const HOOK_FILE = path.resolve(__dirname, 'agent-card-titles.js');
const EVENTS = ['UserPromptSubmit', 'Stop', 'SessionEnd'];
const STATUS = {
  UserPromptSubmit: 'Titling session card...',
  Stop: 'Reordering agent cards...',
  SessionEnd: 'Stamping agent card...',
};

// ------------------------------------------------------------------ args

const argv = process.argv.slice(2);
const has = (flag) => argv.includes(flag);
const valueOf = (flag) => {
  const i = argv.indexOf(flag);
  return i === -1 ? null : argv[i + 1];
};

const uninstall = has('--uninstall');
const dryRun = has('--dry-run');
const recompute = has('--recompute');
const nodeExe = valueOf('--node') || process.execPath;
const home = valueOf('--home') || process.env.CLAUDE_CONFIG_DIR || path.join(os.homedir(), '.claude');
const settingsFile = path.join(home, 'settings.json');

// ------------------------------------------------------------------ helpers

function readSettings() {
  if (!fs.existsSync(settingsFile)) return {};
  const raw = fs.readFileSync(settingsFile, 'utf8').trim();
  if (!raw) return {};
  try { return JSON.parse(raw); } catch (e) {
    console.error('! ' + settingsFile + ' is not valid JSON — fix it first.\n  ' + e.message);
    process.exit(1);
  }
}

// Ours if it invokes a file named agent-card-titles.js, wherever it lives.
function isOurs(hook) {
  const hay = [hook.command, ...(hook.args || [])].join(' ');
  return hay.includes('agent-card-titles.js');
}

function stripOurs(settings) {
  let removed = 0;
  const hooks = settings.hooks || {};

  for (const event of Object.keys(hooks)) {
    if (!Array.isArray(hooks[event])) continue;

    for (const group of hooks[event]) {
      if (!group || !Array.isArray(group.hooks)) continue;
      const before = group.hooks.length;
      group.hooks = group.hooks.filter((h) => !isOurs(h));
      removed += before - group.hooks.length;
    }

    // Drop groups we emptied, and the event key if nothing else uses it.
    hooks[event] = hooks[event].filter((g) => g && Array.isArray(g.hooks) && g.hooks.length > 0);
    if (hooks[event].length === 0) delete hooks[event];
  }

  return removed;
}

function addOurs(settings) {
  settings.hooks = settings.hooks || {};

  for (const event of EVENTS) {
    settings.hooks[event] = settings.hooks[event] || [];

    const entry = {
      type: 'command',
      command: nodeExe,          // exec form: spawned directly, never through a shell,
      args: [HOOK_FILE],         // so Windows backslashes and spaces survive untouched
      statusMessage: STATUS[event],
    };

    // Reuse a matcher-less group if there is one, so we do not fragment the file.
    const group = settings.hooks[event].find((g) => g && !g.matcher && Array.isArray(g.hooks));
    if (group) group.hooks.push(entry);
    else settings.hooks[event].push({ hooks: [entry] });
  }
}

function backup() {
  if (!fs.existsSync(settingsFile)) return null;
  const dest = settingsFile + '.bak';
  fs.copyFileSync(settingsFile, dest);
  return dest;
}

// Retitle every existing card, in every project, without waiting for a hook to fire.
function recomputeAll() {
  const jobsRoot = path.join(home, 'jobs');

  let ids;
  try { ids = fs.readdirSync(jobsRoot); } catch { console.log('no jobs directory — nothing to recompute'); return; }

  const projects = new Map();
  for (const id of ids) {
    let s;
    try { s = JSON.parse(fs.readFileSync(path.join(jobsRoot, id, 'state.json'), 'utf8')); } catch { continue; }
    const cwd = s.originCwd || s.cwd;
    if (cwd) projects.set(String(cwd).toLowerCase(), cwd);
  }

  for (const cwd of projects.values()) {
    // A session id that matches no job, so no card is skipped as "live".
    const payload = JSON.stringify({
      hook_event_name: 'Stop',
      session_id: '00000000-0000-0000-0000-000000000000',
      cwd,
    });
    try { execFileSync(nodeExe, [HOOK_FILE], { input: payload, timeout: 30000 }); }
    catch (e) { console.log('  ! ' + cwd + ': ' + e.message); }
  }

  console.log('recomputed ' + ids.length + ' card(s) across ' + projects.size + ' project(s)');
}

// ------------------------------------------------------------------ main

if (!fs.existsSync(HOOK_FILE)) {
  console.error('! agent-card-titles.js not found next to install.js (' + HOOK_FILE + ')');
  process.exit(1);
}

const settings = readSettings();
const removed = stripOurs(settings);
if (!uninstall) addOurs(settings);

const json = JSON.stringify(settings, null, 2) + '\n';

if (dryRun) {
  console.log(json);
  process.exit(0);
}

if (!fs.existsSync(home)) fs.mkdirSync(home, { recursive: true });
const saved = backup();
fs.writeFileSync(settingsFile, json);

console.log(uninstall ? 'Uninstalled.' : 'Installed.');
console.log('  settings : ' + settingsFile + (saved ? '  (backup: ' + path.basename(saved) + ')' : ''));
if (removed) console.log('  replaced : ' + removed + ' existing registration(s)');
if (!uninstall) console.log('  hook     : ' + HOOK_FILE + '\n  events   : ' + EVENTS.join(', '));

if (recompute && !uninstall) recomputeAll();

if (!uninstall) console.log('\nRestart Claude Code (or open /hooks once) to load the hooks.');
