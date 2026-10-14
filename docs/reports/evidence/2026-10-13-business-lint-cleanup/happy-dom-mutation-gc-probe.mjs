// Run from the ZXUI repository: node --expose-gc --input-type=module - < this-file
import { Window } from 'happy-dom';

if (typeof global.gc !== 'function') throw new Error('Run Node with --expose-gc');

async function probe(collect) {
  const window = new Window();
  const scope = window.document.body.appendChild(window.document.createElement('section'));
  let notices = 0;
  const observer = new window.MutationObserver(() => notices++);
  observer.observe(scope, { attributes: true, attributeFilter: ['data-zx-composition'] });
  await new Promise((resolve) => setTimeout(resolve, 20));
  if (collect) global.gc();
  scope.dataset.zxComposition = 'distance-125';
  await new Promise((resolve) => setTimeout(resolve, 50));
  const result = { collect, notices, observerStillReferenced: !!observer, connected: scope.isConnected };
  observer.disconnect();
  await window.happyDOM.close();
  return result;
}

process.stdout.write(JSON.stringify([await probe(false), await probe(true)], null, 2) + '\n');
