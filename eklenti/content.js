// YouTube Türkçe dublaj: localhost:8790'daki hazır dublajı videoyla senkron çalar.
(() => {
  const BASE = 'http://localhost:8790/';
  const audio = new Audio(); // tek, tekrar kullanılan çalar
  let st = null;   // aktif videonun durumu
  let key = '';    // son kontrol edilen videoId
  let token = 0;   // eski fetch'leri geçersiz kılmak için

  // localhost isteği arka plandan gider: sayfa (youtube.com) yerel ağa doğrudan istek atamaz.
  const bg = (url, json) => new Promise(res => {
    try { chrome.runtime.sendMessage({ url, json }, v => res(chrome.runtime.lastError ? null : v)); } catch { res(null); }
  });

  const store = {
    get: keys => new Promise(res => { try { chrome.storage.local.get(keys, o => res(o || {})); } catch { res({}); } }),
    set: obj => { try { chrome.storage.local.set(obj); } catch {} },
  };

  // start <= t olan son segment ([start, nextStart) aralığı); yoksa -1
  function findSeg(segs, t) {
    let lo = 0, hi = segs.length - 1, ans = -1;
    while (lo <= hi) {
      const m = (lo + hi) >> 1;
      if (segs[m].start <= t) { ans = m; lo = m + 1; } else hi = m - 1;
    }
    return ans;
  }

  // Klibi blob olarak indirir (sunucu Range desteklemese de seek çalışır). Önbellek: mevcut + sonraki.
  function clip(i) {
    const k = st.voice + ':' + i;
    if (!st.cache.has(k)) {
      const f = st.data.segments[i]?.files?.[st.voice];
      st.cache.set(k, !f ? Promise.resolve(null) : bg(BASE + st.id + '/' + f)
        .then(d => d && fetch(d)).then(r => r && r.blob())
        .then(b => b && URL.createObjectURL(b))
        .catch(() => null));
    }
    return st.cache.get(k);
  }

  function prune(keep) {
    for (const [k, p] of st.cache) {
      if (!keep.includes(k)) { st.cache.delete(k); p.then(u => u && URL.revokeObjectURL(u)); }
    }
  }

  async function start(i) {
    const s = st, url = await clip(i);
    if (s !== st || s.cur !== i) return; // bu arada segment/video değişti
    prune([s.voice + ':' + i, s.voice + ':' + (i + 1)]);
    if (i + 1 < s.data.segments.length) clip(i + 1); // sonrakini önceden yükle
    if (!url) return;
    audio.src = url;
    audio.defaultPlaybackRate = audio.playbackRate = s.video.playbackRate;
    // Ofset klip süresini aşarsa tarayıcı sona sabitler: klip "ended" olur, ses çıkmaz.
    const off = s.video.currentTime - s.data.segments[i].start;
    // Önceki klip taştıysa yeni klip baştan çalar (ilk kelimeler kaybolmasın); 3 sn'den fazla gecikmede yetişmek için atlar.
    // ponytail: gecikme ardışık uzun cümlelerde birikebilir, 3 sn tavanı bunu sınırlıyor.
    audio.currentTime = s.late && off < 3 ? 0 : Math.max(0, off);
    s.late = false;
    s.ready = i;
    if (!s.video.paused) audio.play().catch(() => {});
  }

  function tick() {
    if (!st) return;
    const v = st.video;
    const ad = st.player?.classList.contains('ad-showing');
    if (st.voice === 'off' || ad) { audio.pause(); if (ad) st.cur = -1; return; }
    if (Math.abs(v.volume - st.orig) > 0.005) v.volume = st.orig;
    if (v.paused || v.seeking || v.readyState < 3) { audio.pause(); return; } // duraklama/arabellek
    const i = findSeg(st.data.segments, v.currentTime);
    // Klip yuvasından uzunsa önce bitsin (seek ve ses değişimi ready'yi -1 yapıp hemen keser).
    if (i !== st.cur && st.ready >= 0 && !audio.ended && audio.currentTime < audio.duration) {
      if (audio.paused) audio.play().catch(() => {});
      st.late = true;
      return;
    }
    if (i !== st.cur) {
      st.cur = i; st.ready = -1; audio.pause();
      if (i >= 0) start(i);
    } else if (i >= 0 && st.ready === i && audio.paused && !audio.ended) {
      audio.play().catch(() => {}); // duraklatmadan sonra devam
    }
  }

  function restoreVol() {
    if (st.savedVol != null) { st.video.volume = st.savedVol; st.savedVol = null; }
  }

  function setVoice(v) {
    st.voice = v; st.cur = st.ready = -1;
    audio.pause(); prune([]);
    if (v === 'off') restoreVol();
    else if (st.savedVol == null) st.savedVol = st.video.volume;
    tick();
  }

  function buildUI() {
    const ui = document.createElement('div');
    ui.style.cssText = 'position:absolute;top:12px;right:12px;z-index:9999;display:flex;gap:8px;align-items:center;' +
      'padding:6px 10px;border-radius:8px;background:rgba(0,0,0,.7);color:#fff;font:13px Roboto,Arial,sans-serif';
    const sel = document.createElement('select');
    sel.title = 'Türkçe dublaj';
    sel.style.cssText = 'background:#222;color:#fff;border:1px solid #555;border-radius:4px;font:inherit';
    for (const [v, label] of [['off', 'Kapalı'], ...Object.entries(st.data.voices)]) sel.add(new Option(label, v));
    sel.value = st.voice;
    sel.onchange = () => { store.set({ dubVoice: sel.value }); setVoice(sel.value); };
    const txt = document.createElement('span');
    const rng = document.createElement('input');
    rng.type = 'range'; rng.min = 0; rng.max = 30; rng.value = Math.round(st.orig * 100);
    rng.title = 'Orijinal ses seviyesi';
    rng.style.width = '80px';
    const show = () => { txt.textContent = 'Orijinal ses %' + rng.value; };
    rng.oninput = () => { st.orig = rng.value / 100; store.set({ dubOrig: st.orig }); show(); tick(); };
    show();
    ui.append(sel, txt, rng);
    // Tıklama/klavye olayları oynatıcıya (oynat/duraklat, kısayollar) gitmesin.
    for (const e of ['click', 'dblclick', 'mousedown', 'mouseup', 'pointerdown', 'pointerup', 'keydown', 'keyup', 'wheel']) {
      ui.addEventListener(e, ev => ev.stopPropagation());
    }
    return ui;
  }

  function teardown() {
    if (!st) return;
    audio.pause(); audio.removeAttribute('src'); audio.load();
    restoreVol(); clearInterval(st.timer); st.ac.abort(); st.ui.remove(); prune([]);
    st = null;
  }

  async function load(id, video, my) {
    let data;
    data = await bg(BASE + id + '/manifest.json', true);
    if (!data) return; // sunucu yok ya da dublaj yok: sessiz kal
    const saved = await store.get(['dubVoice', 'dubOrig']);
    if (my !== token || !Array.isArray(data?.segments) || !data.voices) return;
    data.segments.sort((a, b) => a.start - b.start);
    const ac = new AbortController();
    st = {
      id, data, video, ac, player: video.closest('#movie_player'), cache: new Map(),
      cur: -1, ready: -1, savedVol: null, voice: 'off',
      orig: typeof saved.dubOrig === 'number' ? saved.dubOrig : 0.1,
    };
    const on = (ev, fn) => video.addEventListener(ev, fn, { signal: ac.signal });
    on('pause', () => audio.pause());
    on('play', tick);
    on('playing', tick);
    on('seeking', () => { audio.pause(); st.cur = st.ready = -1; st.late = false; });
    on('seeked', tick);
    on('ratechange', () => { audio.playbackRate = video.playbackRate; });
    st.ui = buildUI();
    st.player?.append(st.ui);
    st.timer = setInterval(tick, 100);
    const v = data.voices[saved.dubVoice] ? saved.dubVoice : 'off';
    st.ui.querySelector('select').value = v;
    setVoice(v);
  }

  function check() {
    const id = location.pathname === '/watch' ? new URLSearchParams(location.search).get('v') : null;
    const video = document.querySelector('#movie_player video');
    if (st && !st.video.isConnected) key = ''; // oynatıcı yeniden kuruldu
    const k = id && video ? id : '';
    if (k !== key) {
      key = k; token++; teardown();
      if (k) load(id, video, token);
    } else if (st && !st.ui.isConnected) {
      st.player = st.video.closest('#movie_player');
      st.player?.append(st.ui);
    }
  }

  document.addEventListener('yt-navigate-start', () => { key = ''; token++; teardown(); });
  document.addEventListener('yt-navigate-finish', check);
  setInterval(check, 1000); // URL değişimi ve geç yüklenen oynatıcı için
  check();
  console.log('[yt-dublaj] eklenti yüklendi');
})();
