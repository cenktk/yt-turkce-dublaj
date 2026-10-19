# YouTube Türkçe Dublaj — Kurulum

1. Chrome'da `chrome://extensions` adresini aç.
2. Sağ üstteki **Geliştirici modu** anahtarını aç.
3. **Paketlenmemiş öğe yükle** düğmesine bas.
4. Bu repodaki `eklenti` klasörünü seç.
5. Terminalde repo klasörüne geç. Sonraki komutlar bu klasöre göre yazıldı.
6. Yerel sunucuyu başlat ve terminali açık bırak:

   ```
   python3 hazirla.py serve --port 8790
   ```

7. İngilizce bir videoyu YouTube'da aç. Oynatıcının sağ üstünde dublaj kutusu çıkar.
8. Listeden sesi seç: "Erkek (Oncel)" ya da "Kadın (Nisa)". Sonra **Türkçe dublaj hazırla** düğmesine bas. Önce ilk 90 saniye hazırlanır, sonra videonun tamamı.
9. Dublajı hazır videoda listede "(hazırla)" yazan ses henüz üretilmemiştir. Onu seçersen o ses de hazırlanır. "Kapalı" dublajı kapatır.
10. "Orijinal ses" kaydırıcısıyla videonun kendi sesini %0–30 arasında ayarla.

## Notlar

- Kutu çıkmazsa sunucunun çalıştığını kontrol et, sonra sayfayı yenile.
- Eklenti yalnız `localhost:8790` adresine bağlanır. İstekleri eklentinin arka plan betiği (`background.js`) yapar, çünkü youtube.com sayfası localhost'a doğrudan istek atamaz.
- Eklenti dosyalarını değiştirirsen `chrome://extensions` sayfasında eklentinin yenile düğmesine bas.
- Seçtiğin ses ve orijinal ses seviyesi bir sonraki videoda da geçerli olur.
