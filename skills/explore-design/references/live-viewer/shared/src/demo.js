// Demo module for the live-viewer template: an ES module on purpose, so the template shows the
// prep tool's bundle route (tools/prep.config.json -> shared/mock.bundle.js, window.Mock).
// Reads its data from window.__MOCK_DATA.demo, which the prep tool embeds from demo-data.json.
export function renderList(el) {
  const items = (window.__MOCK_DATA && window.__MOCK_DATA.demo && window.__MOCK_DATA.demo.items) || [];
  el.innerHTML = items.map((it) => `<li class="card"><h3>${it.name}</h3><p>${it.note}</p><p class="price">${it.price}</p></li>`).join('');
  return items.length;
}

export const demoVersion = 1;
