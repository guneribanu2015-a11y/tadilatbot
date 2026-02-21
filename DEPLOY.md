# 🚀 Streamlit Cloud Deploy Rehberi

## Yerel Geliştirme (.env)

1. `.env` dosyasını aç, API key'ini yaz:
   ```
   ANTHROPIC_API_KEY=sk-ant-xxxxx
   ```

2. Uygulamayı başlat:
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```

---

## Streamlit Cloud'a Deploy (başkasına link göndermek için)

### Adım 1 — GitHub'a yükle
```bash
git init
git add app.py requirements.txt .gitignore
# NOT: .env ve .streamlit/secrets.toml ekleme! .gitignore halleder.
git commit -m "ilk commit"
git branch -M main
git remote add origin https://github.com/KULLANICI_ADIN/tadilat-app.git
git push -u origin main
```

### Adım 2 — Streamlit Cloud hesabı
- https://share.streamlit.io adresine git
- GitHub hesabınla giriş yap
- "New app" → repoyu seç → `app.py` → Deploy

### Adım 3 — API Key'i güvenli ekle
Deploy ekranında veya sonradan:
- "Settings" → "Secrets" sekmesi
- Şunu yapıştır:
  ```toml
  ANTHROPIC_API_KEY = "sk-ant-xxxxx"
  ```
- Save → Reboot app

### Sonuç
`https://KULLANICI-tadilat-app.streamlit.app` gibi bir link alırsın.
Bu linki test kullanıcılarına gönderebilirsin.

---

## Önemli Notlar
- `.env` dosyasını GitHub'a **asla** gönderme (.gitignore hallediyor)
- Streamlit Cloud ücretsiz planda uygulama 7 gün aktif kalır,
  sonra uyku moduna girer (ilk açılışta ~30 sn bekler)
- Veri session'da tutuluyor — sayfa yenilenince sıfırlanır
  (Supabase ekleyince bu sorun çözülecek)
