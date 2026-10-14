# YouTube Türkçe Dublaj — Kurulum

1. Chrome'da `chrome://extensions` adresini aç.
2. Sağ üstteki **Geliştirici modu** anahtarını aç.
3. **Paketlenmemiş öğe yükle** düğmesine bas.
4. Bu repodaki `eklenti` klasörünü seç.
5. Terminalde repo klasörüne geç. Sonraki komutlar bu klasöre göre yazıldı.
6. Videonun dublajını hazırla:

   ```
   python3 hazirla.py <youtube-url>
   ```

7. Yerel sunucuyu başlat ve terminali açık bırak:

   ```
   python3 hazirla.py serve --port 8790
   ```

8. Videoyu YouTube'da aç. Oynatıcının sağ üstünde dublaj kutusu çıkar.
9. Listeden bir ses seç: "Kadın (Nisa)" ya da "Erkek (Oncel)". "Kapalı" dublajı kapatır.
10. "Orijinal ses" kaydırıcısıyla videonun kendi sesini %0–30 arasında ayarla.

## Notlar

- Kutu çıkmazsa sunucunun çalıştığını kontrol et, sonra sayfayı yenile.
- Eklenti yalnız `localhost:8790` adresine bağlanır. İstekleri eklentinin arka plan betiği (`background.js`) yapar, çünkü youtube.com sayfası localhost'a doğrudan istek atamaz.
- Eklenti dosyalarını değiştirirsen `chrome://extensions` sayfasında eklentinin yenile düğmesine bas.
- Seçtiğin ses ve orijinal ses seviyesi bir sonraki videoda da geçerli olur.
