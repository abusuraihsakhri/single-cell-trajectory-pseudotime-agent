import { readFileSync } from 'node:fs';
import { Script, createContext, runInContext } from 'node:vm';
import test from 'node:test';
import assert from 'node:assert/strict';

const html = readFileSync(new URL('../web/index.html', import.meta.url), 'utf8');
const match = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(match, 'browser app must contain an inline script');

function fixture() {
  const values = {
    outputConsole: { textContent: '' },
    task_id: { value: 'T1' },
    target_id: { value: 'KEY-1' },
    primary_metric: { value: '10' },
    secondary_metric: { value: '2' },
    status_descriptor: { value: 'NOMINAL' },
    is_critical: { checked: false },
    'm-tasks': { textContent: '0' },
    'm-status': { textContent: 'READY' },
  };
  const ctx = createContext({
    document: { getElementById: id => {
      if (!values[id]) throw new Error('Missing UI node: ' + id);
      return values[id];
    } },
  });
  new Script(match[1]).runInContext(ctx);
  return { values, evaluate: () => runInContext('runAudit()', ctx) };
}

test('HTML embedded JavaScript parses', () => {
  new Script(match[1]);
});

test('nominal analysis is computed locally', () => {
  const f = fixture();
  f.evaluate();
  assert.equal(JSON.parse(f.values.outputConsole.textContent).overall_urgency, 'ROUTINE');
  assert.equal(f.values['m-tasks'].textContent, '1');
});

test('critical flag triggers correct status without fake signature', () => {
  const f = fixture();
  f.values.is_critical.checked = true;
  f.evaluate();
  const result = JSON.parse(f.values.outputConsole.textContent);
  assert.equal(result.overall_urgency, 'CRITICAL_STAT_PANIC');
  assert.equal(result.mode, 'BROWSER_RULE_PREVIEW_NOT_SIGNED');
  assert.equal('audit_hash' in result, false);
});

test('invalid values and possible identifiers are rejected', () => {
  const f = fixture();
  f.values.primary_metric.value = '';
  f.evaluate();
  assert.match(f.values.outputConsole.textContent, /Validation error/);
  assert.equal(f.values['m-tasks'].textContent, '0');
  f.values.primary_metric.value = '2';
  f.values.task_id.value = 'MRN-123456';
  f.evaluate();
  assert.match(f.values.outputConsole.textContent, /identifier/);
});
