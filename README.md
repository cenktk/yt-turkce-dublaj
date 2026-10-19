# YouTube Türkçe Dublaj

İngilizce bir YouTube videosu için önceden Türkçe dublaj hazırlar. Chrome eklentisi dublajı videoyla senkron çalar.

Akış: YouTube altyazısı (yt-dlp) → Türkçe çeviri (Claude Code, `claude -p`) → seslendirme (Alania v2 TTS) → eklenti.

## Gerekenler

- Python 3.9+
- `yt-dlp` ve `ffmpeg` (macOS: `brew install yt-dlp ffmpeg`)
- [Claude Code](https://claude.com/claude-code) kurulu ve giriş yapılmış olmalı (`claude` komutu çalışmalı)
- Alania v2 TTS API anahtarı (`PATIENTDESK_API_KEY`)

## Kurulum

1. `.env.example` dosyasını `.env` adıyla kopyala.
2. `.env` içine kendi API anahtarını yaz. Bu dosya repoya girmez.
3. Eklentiyi Chrome'a yükle: `eklenti/KURULUM.md` dosyasındaki adımları izle.

## Kullanım

```bash
python3 hazirla.py <youtube-url> --ses nisa,oncel
```

```bash
python3 hazirla.py serve --port 8790
```

İlk komut dublajı `dublaj/<videoId>/` klasörüne yazar. İkinci komut eklentinin okuduğu yerel sunucuyu açar.

Sunucu açıkken URL vermek gerekmez. Dublajı olmayan videoda eklenti bir ses listesi ve "Türkçe dublaj hazırla" düğmesi gösterir. Düğme önce ilk 90 saniyeyi, sonra videonun tamamını hazırlar. Dublajı hazır videoda eksik ses listeden seçilerek sonradan eklenir.

Kurulumu Claude Code ile yapmak için repo linkini Claude'a verin. Adımlar `CLAUDE.md` dosyasında.

- Yalnız ilk N saniyeyi denemek için: `--ilk 60`
- Tek ses için: `--ses nisa`

## Maliyet

Ses başına yaklaşık video uzunluğu kadar karakter harcanır. 15 dakikalık bir video ses başına ~16 bin karakter tutar. Uzun videodan önce `--ilk 60` ile dene.

## Notlar

- Altyazısı olmayan videoda çalışmaz.
- Eklenti yalnız `localhost:8790` adresine bağlanır.
