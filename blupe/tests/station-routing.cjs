const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const title = process.argv[2];
const script = fs.readFileSync(process.argv[3], 'utf8');
const runner = fs.readFileSync(process.argv[4], 'utf8');
const sandbox = {window: {}, document: {title}};
vm.createContext(sandbox);
vm.runInContext(script, sandbox);
// Exercise the pinned shared picker's actual startup selection, before sessionReady.
const initial = runner.match(/let selectedRobot = ([^;]+);/)[0];
const start = runner.indexOf('  async function loadRobotSelector() {');
const end = runner.indexOf('  async function start() {', start);
const selector = {replaceChildren(...items) {this.options = items;}, append() {}};
sandbox.$ = () => selector;
sandbox.document.createElement = () => ({});
sandbox.location = {search: ''};
sandbox.URLSearchParams = URLSearchParams;
sandbox.CustomEvent = class {};
sandbox.window.dispatchEvent = () => {};
sandbox.api = async () => ({selected: title.endsWith('YAM1') ? 'yam-1' : 'robot-ba8413962083809c', robots: [
 {id: 'yam-1', name: 'YAM1', connected: true},
 {id: 'robot-ba8413962083809c', name: 'Robo-house', connected: null}]});
vm.runInContext(initial + runner.slice(start, end) + '\nloadRobotSelector().then(() => { result = selectedRobot; });', sandbox);
setImmediate(() => {
 assert.equal(sandbox.result, title.endsWith('YAM1') ? 'yam-1' : 'robot-ba8413962083809c',
  'Station served by this origin must win over generic fleet default/connectivity ordering');
});
