const fs = require('fs');
const os = require('os');
const path = require('path');

const workTmp = path.resolve(__dirname, '..', '.tmp');
fs.mkdirSync(workTmp, {recursive: true});
os.tmpdir = () => workTmp;
process.env.TMPDIR = workTmp;

const ignorable = new Set(['EPERM', 'ENOENT', 'EACCES']);
const swallow = (fn) =>
  function (...args) {
    try {
      const r = fn.apply(this, args);
      if (r && typeof r.then === 'function') {
        return r.catch((e) => {
          if (ignorable.has(e.code)) return undefined;
          throw e;
        });
      }
      return r;
    } catch (e) {
      if (ignorable.has(e.code)) return undefined;
      throw e;
    }
  };

for (const name of ['unlinkSync', 'rmSync', 'rmdirSync']) {
  if (typeof fs[name] === 'function') fs[name] = swallow(fs[name]);
}
if (fs.promises) {
  for (const name of ['unlink', 'rm', 'rmdir']) {
    if (typeof fs.promises[name] === 'function') fs.promises[name] = swallow(fs.promises[name]);
  }
}
