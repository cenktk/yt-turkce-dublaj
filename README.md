# YouTube Türkçe Dublaj

İngilizce bir YouTube videosu için önceden Türkçe dublaj hazırlar. Chrome eklentisi dublajı videoyla senkron çalar.

Akış: YouTube altyazısı (yt-dlp) → Türkçe çeviri (Claude Code, `claude -p`) → seslendirme (Alania v2 TTS) → eklenti.

## Gerekenler

- macOS (Linux denenmedi). Python 3.9+
- `yt-dlp` ve `ffmpeg` (`brew install yt-dlp ffmpeg`)
- [Claude Code](https://claude.com/claude-code) kurulu ve giriş yapılmış olmalı (`claude` komutu çalışmalı)
- Alania v2 TTS API anahtarı (`PATIENTDESK_API_KEY`). Anahtarı https://speech.patientdesk.ai/tr adresinden alın.

## Kurulum

En kolayı: repo linkini Claude Code'a verin, adımlar `CLAUDE.md` dosyasında. Elle:

1. Repoyu **Documents veya Desktop dışına** klonlayın. macOS arka plan servislerine o klasörlerde erişim vermez, sunucu oradan otomatik başlayamaz.
   ```bash
   git clone https://github.com/cenktk/yt-turkce-dublaj.git ~/yt-turkce-dublaj
   ```
2. `.env.example` dosyasını `.env` adıyla kopyalayın, içine kendi API anahtarınızı yazın. Bu dosya repoya girmez.
3. Sunucuyu oturum açılışında kendiliğinden başlayan bir servis olarak kurun (bir kez):
   ```bash
   sh ~/yt-turkce-dublaj/otomatik_baslat.sh
   ```
   Son satır `tamam: sunucu her girişte kendiliğinden açılır` olmalı. Sunucu çökerse macOS yeniden başlatır. Günlük: `dublaj/serve.log`.
4. Eklentiyi Chrome'a yükleyin: `eklenti/KURULUM.md`. Eklenti yalnız `localhost:8790` ile konuşur.

Servisi kaldırmak: `launchctl bootout gui/$(id -u)/com.yt-dublaj && rm ~/Library/LaunchAgents/com.yt-dublaj.plist`

## Kullanım

Bir İngilizce YouTube videosu açın. Oynatıcının sağ üstünde bir kutu çıkar:

- **Dublajı yoksa:** ses listesi ve **Türkçe dublaj hazırla** düğmesi. Düğme önce ilk 90 saniyeyi, sonra tamamını hazırlar. Kutu "hazırlanıyor…" derken bekleyin, bitince ses kendiliğinden seçilir.
- **Dublajı varsa:** ses seçici ve orijinal ses seviyesi kaydırıcısı. Henüz yapılmamış ses listede "(hazırla)" ile görünür, seçince o da üretilir.
- **Kutu yoksa:** sunucu kapalı demektir. `curl -s -X POST -H 'X-Dublaj: 1' http://localhost:8790/durum/x` yanıt vermiyorsa adım 3'ü tekrar çalıştırın. Sunucu açıksa sayfayı yenileyin.

Komut satırından da hazırlanır:

```bash
python3 hazirla.py <youtube-url> --ses nisa,oncel      # dublaj/<videoId>/ klasörüne yazar
python3 hazirla.py <youtube-url> --ses mini --ilk 60    # ücretsiz sesle yalnız ilk 60 sn
```

## Nasıl çalar

- Her çeviri cümlesi ayrı bir mp3 kliptir, eklenti videonun zamanına göre klibi başlatır. Orijinal ses varsayılan %10'a iner.
- Türkçe cümle İngilizcesinden uzun kalırsa klip en çok 1.35 kat hızlandırılır. Yine sığmazsa eklenti **videoyu yavaşlatır** (en az %70 hız), dublaj sesi sizin seçtiğiniz hızda kalır. Böylece gecikme birikmez.
- Çeviri sesli okunacağı için rakamlar Türkçe yazıyla çevrilir ("2023" → "iki bin yirmi üç") ve parantezli açıklama kullanılmaz.
- Çeviri `dublaj/<videoId>/ceviri.json` dosyasında saklanır. Bir videoyu yeni istem kurallarıyla yeniden çevirmek için o dosyayı silin.

## Maliyet

**Ücretsiz (Antalia Mini)** sesi karakter harcamaz. Anahtar yine gerekir ama bu ses için ücret çıkmaz.

Nisa ve Oncel seslerinde ses başına yaklaşık konuşma metni kadar karakter harcanır. 15 dakikalık bir video ses başına ~16 bin karakter tutar. Uzun videodan önce `--ilk 60` ile deneyin.

## Notlar

- Altyazısı olmayan videoda çalışmaz.
- Eklenti kodunu güncellediyseniz (`git pull`) `chrome://extensions` sayfasında eklentiyi yenileyin, sonra YouTube sayfasını yenileyin. Chrome yüklediği kopyayı çalıştırır.
- Repo klasörünü taşıdıysanız eklentiyi Chrome'dan kaldırıp yeni yoldan yükleyin ve adım 3'ü tekrar çalıştırın.
- Benzer, daha büyük bir proje: [DubWorld](https://github.com/alexturkey/dubworld) videodan yerel modellerle dublajlı MP4 üretir. Rakam yazımı ve video yavaşlatma fikri oradan alındı.
