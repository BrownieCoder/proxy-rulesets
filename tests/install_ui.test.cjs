'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const read = (file) => fs.readFileSync(path.join(root, file), 'utf8');
const catalog = JSON.parse(read('install/catalog.json'));

test('browser catalog and JSON expose the same services and clients', () => {
  const context = {window: {}};
  vm.runInNewContext(read('install/catalog.js'), context);
  assert.equal(JSON.stringify(context.window.INSTALL_CATALOG), JSON.stringify(catalog));
  assert.equal(catalog.services.length, JSON.parse(read('catalog/services.json')).length);
  assert.equal(new Set(catalog.services.map(s => s.id)).size, catalog.services.length);
});

test('every guide is a readable local HTML page with a real anchor', () => {
  for (const record of [...catalog.services, ...catalog.clients]) {
    const [file, fragment] = record.guideUrl.split('#');
    const resolved = path.resolve(root, 'install', file);
    assert.ok(resolved.startsWith(root + path.sep));
    const html = fs.readFileSync(resolved, 'utf8');
    assert.match(html, /<!doctype html>/i);
    if (fragment) assert.ok(html.includes(`id="${fragment}"`), record.guideUrl);
  }
  for (const service of catalog.services) {
    const url = new URL(service.rawUrl);
    assert.equal(url.host, 'raw.githubusercontent.com');
    assert.equal(url.pathname, `/${catalog.repository}/${catalog.branch}/${service.path}`);
    assert.ok(fs.existsSync(path.join(root, service.path)));
  }
});

test('module launch and fallback URL are identical after decoding', () => {
  for (const service of catalog.services.filter(s => s.module)) {
    const module = service.module;
    const scheme = new URL(module.schemeUrl);
    assert.equal(scheme.protocol, 'shadowrocket:');
    assert.equal(scheme.hostname, 'install');
    assert.equal(scheme.searchParams.get('module'), module.rawUrl);
    assert.ok(fs.existsSync(path.join(root, module.path)));
    if (module.published) {
      const proof = JSON.parse(read('catalog/online-verification.json')).results;
      assert.ok(proof.some(r => r.url === module.rawUrl && r.status === 200));
    }
  }
  for (const client of catalog.clients) assert.equal(client.fallback.length, 3);
});

test('page scripts and styles are local, and required DOM targets exist', () => {
  const html = read('install/index.html');
  for (const match of html.matchAll(/(?:src|href)="([^"]+\.(?:js|css))"/g)) {
    assert.ok(!match[1].includes('://'));
    assert.ok(fs.existsSync(path.join(root, 'install', match[1])));
  }
  const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]);
  assert.equal(new Set(ids).size, ids.length);
  for (const match of read('install/app.js').matchAll(/byId\("([^"]+)"\)/g)) {
    assert.ok(ids.includes(match[1]), `missing DOM target ${match[1]}`);
  }
});
