// content.js'in localhost isteklerini yapar. Ses dosyası data URL olarak döner.
chrome.runtime.onMessage.addListener((m, _sender, send) => {
  fetch(m.url, m.post ? { method: 'POST', headers: { 'X-Dublaj': '1' } } : undefined)
    .then(async r => {
      if (!r.ok) return send(null);
      if (m.json) return send(await r.json());
      const b = await r.blob();
      const fr = new FileReader();
      fr.onload = () => send(fr.result);
      fr.readAsDataURL(b);
    })
    .catch(() => send(null));
  return true; // yanıt asenkron
});
