import streamlit as st
import anthropic
import json
import uuid
import urllib.parse
import os
from datetime import datetime

# API key: önce Streamlit secrets, sonra .env, sonra environment variable
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def get_api_key():
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except:
        return os.getenv("ANTHROPIC_API_KEY", "")

st.set_page_config(
    page_title="TeklifAI — Tadilat Teklif Asistanı",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Session state başlat ──────────────────────────────────────────
if "firma_profili" not in st.session_state:
    st.session_state.firma_profili = None
if "aktif_teklif" not in st.session_state:
    st.session_state.aktif_teklif = {}
if "teklifler" not in st.session_state:
    st.session_state.teklifler = []
if "sayfa" not in st.session_state:
    st.session_state.sayfa = "ana_sayfa"
if "teklif_adim" not in st.session_state:
    st.session_state.teklif_adim = 1
if "birim_fiyatlar" not in st.session_state:
    st.session_state.birim_fiyatlar = [
        # 1. Kırım ve Hazırlık
        {"kalem": "Kırım işleri",                          "birim": "gün",  "fiyat": 0},
        {"kalem": "Moloz atımı",                           "birim": "adet", "fiyat": 0},
        {"kalem": "Self-leveling akıllı şap",              "birim": "m²",   "fiyat": 0},
        # 2. Seramik ve Zemin Kaplama
        {"kalem": "Seramik zemin kaplaması (A tipi)",      "birim": "m²",   "fiyat": 0},
        {"kalem": "Seramik zemin kaplaması (B tipi)",      "birim": "m²",   "fiyat": 0},
        {"kalem": "Seramik duvar kaplaması",               "birim": "m²",   "fiyat": 0},
        {"kalem": "Laminat parke kaplaması",               "birim": "m²",   "fiyat": 0},
        {"kalem": "Süpürgelik (lake, yüksek)",             "birim": "mt",   "fiyat": 0},
        # 3. Duvar ve Tavan
        {"kalem": "Alçıpan duvar imalatı",                 "birim": "m²",   "fiyat": 0},
        {"kalem": "Asma tavan / alçıpan havuz",            "birim": "m²",   "fiyat": 0},
        {"kalem": "Kartonpiyer / stropiyer",               "birim": "mt",   "fiyat": 0},
        # 4. Boya
        {"kalem": "İç cephe boyası",                       "birim": "m²",   "fiyat": 0},
        {"kalem": "Duvar kağıdı kaplaması",                "birim": "m²",   "fiyat": 0},
        # 5. Mutfak
        {"kalem": "Mutfak dolapları",                      "birim": "mt",   "fiyat": 0},
        {"kalem": "Mutfak tezgahı (taban)",                "birim": "mt",   "fiyat": 0},
        {"kalem": "Mutfak tezgahı (duvar)",                "birim": "mt",   "fiyat": 0},
        {"kalem": "Mutfak evyesi",                         "birim": "adet", "fiyat": 0},
        {"kalem": "Mutfak lavabo bataryası",               "birim": "adet", "fiyat": 0},
        # 6. Banyo
        {"kalem": "Gömme rezervuar ve kapağı",             "birim": "adet", "fiyat": 0},
        {"kalem": "Asma klozet ve kapağı",                 "birim": "adet", "fiyat": 0},
        {"kalem": "Duş teknesi 90x90",                     "birim": "adet", "fiyat": 0},
        {"kalem": "Duşakabin 90x90",                       "birim": "adet", "fiyat": 0},
        {"kalem": "Duş bataryası ve duş başlığı",          "birim": "adet", "fiyat": 0},
        {"kalem": "Banyo dolabı",                          "birim": "adet", "fiyat": 0},
        {"kalem": "Lavabo bataryası",                      "birim": "adet", "fiyat": 0},
        {"kalem": "Ankastre taharet musluğu",              "birim": "adet", "fiyat": 0},
        {"kalem": "Aksesuarlar (havluluk, kagitlik)",      "birim": "adet", "fiyat": 0},
        {"kalem": "Tesisat boruları",                      "birim": "adet", "fiyat": 0},
        {"kalem": "Tesisat ve montaj işçiliği",            "birim": "adet", "fiyat": 0},
        # 7. Elektrik ve Aydınlatma
        {"kalem": "Elektrik kablo yenileme",               "birim": "m²",   "fiyat": 0},
        {"kalem": "Sigorta panosu ve şalterler",           "birim": "adet", "fiyat": 0},
        {"kalem": "Anahtar ve priz grubu",                 "birim": "adet", "fiyat": 0},
        {"kalem": "Aydınlatma armatürü montajı",           "birim": "adet", "fiyat": 0},
        {"kalem": "Internet/Data hattı (CAT6)",            "birim": "mt",   "fiyat": 0},
        # 8. Isınma ve İklimlendirme
        {"kalem": "Radyatör yenileme",                     "birim": "adet", "fiyat": 0},
        {"kalem": "Kombi / kazan montajı",                 "birim": "adet", "fiyat": 0},
        {"kalem": "Klima altyapısı (bakır boru)",          "birim": "mt",   "fiyat": 0},
        # 9. Kapı ve Güvenlik
        {"kalem": "Ahşap oda kapısı",                      "birim": "adet", "fiyat": 0},
        {"kalem": "Çelik kapı (giriş)",                    "birim": "adet", "fiyat": 0},
        {"kalem": "Kapı kolu ve kilit sistemi",            "birim": "adet", "fiyat": 0},
        {"kalem": "PVC pencere (çift cam)",                "birim": "m²",   "fiyat": 0},
    ]
if "odeme_planlari" not in st.session_state:
    st.session_state.odeme_planlari = [
        {"ad": "Klasik 3'lü",  "plan": "%30 Peşinat — %40 Kaba İnşaat Bitimi — %30 Teslimat"},
        {"ad": "Yarı Yarıya",  "plan": "%50 Peşinat — %50 Teslimat"},
        {"ad": "Üçe Bölüm",    "plan": "%33 Başlangıç — %33 Ara — %34 Teslimat"},
        {"ad": "Peşin",        "plan": "%100 Peşinat"},
    ]

# ── Sidebar ───────────────────────────────────────────────────────
with st.sidebar:
    st.title("🏗️ TeklifAI")
    st.divider()

    if st.button("🏠 Ana Sayfa",      use_container_width=True):
        st.session_state.sayfa = "ana_sayfa"; st.rerun()
    if st.button("➕ Yeni Teklif Ver", use_container_width=True):
        st.session_state.sayfa = "yeni_teklif"
        st.session_state.aktif_teklif = {}
        st.session_state.teklif_adim = 1
        st.rerun()
    if st.button("📋 Tekliflerim",    use_container_width=True):
        st.session_state.sayfa = "teklifler"; st.rerun()
    if st.button("⚙️ Firma Ayarları", use_container_width=True):
        st.session_state.sayfa = "ayarlar"; st.rerun()

    st.divider()
    st.caption("v0.1 — MVP")

# ══════════════════════════════════════════════════════════════════
# SAYFA: ANA SAYFA
# ══════════════════════════════════════════════════════════════════
def sayfa_ana():
    st.title("Hoş geldin 👋")

    if not st.session_state.firma_profili:
        st.info("Başlamak için önce firma profilini kur.")
        if st.button("⚙️ Firma Kurulumuna Git", type="primary"):
            st.session_state.sayfa = "ayarlar"; st.rerun()
        return

    firma = st.session_state.firma_profili
    st.subheader(firma["ad"])

    teklifler = st.session_state.teklifler
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Toplam Teklif", len(teklifler))
    c2.metric("Onaylanan", len([t for t in teklifler if t.get("durum") == "Onaylandı"]))
    c3.metric("Bekleyen",  len([t for t in teklifler if t.get("durum") == "Gönderildi"]))
    c4.metric("Onaylanan Ciro", f"{sum(t.get('toplam_tutar',0) for t in teklifler if t.get('durum')=='Onaylandı'):,.0f} ₺")

    st.divider()
    if st.button("➕ Yeni Teklif Ver", type="primary"):
        st.session_state.sayfa = "yeni_teklif"
        st.session_state.aktif_teklif = {}
        st.session_state.teklif_adim = 1
        st.rerun()

    if teklifler:
        st.subheader("Son Teklifler")
        RENK = {"Taslak":"🟡","Gönderildi":"🔵","İncelendi":"🟠","Onaylandı":"🟢","Reddedildi":"🔴"}
        for t in reversed(teklifler[-5:]):
            c1, c2, c3, c4 = st.columns([2,2,1,1])
            c1.write(f"**{t.get('musteri_ad','-')}**")
            proje = ", ".join(t.get("proje_turu",[]))
            c2.write(proje[:40]+"..." if len(proje)>40 else proje)
            c3.write(f"{t.get('toplam_tutar',0):,.0f} ₺")
            c4.write(f"{RENK.get(t.get('durum','Taslak'),'⚪')} {t.get('durum','Taslak')}")

# ══════════════════════════════════════════════════════════════════
# SAYFA: AYARLAR
# ══════════════════════════════════════════════════════════════════
def sayfa_ayarlar():
    st.title("⚙️ Firma Ayarları")
    firma = st.session_state.firma_profili or {}
    tab1, tab2, tab3 = st.tabs(["🏢 Firma Bilgileri", "💰 Birim Fiyatlar", "📅 Ödeme Planları"])

    with tab1:
        ad       = st.text_input("Firma Adı",     value=firma.get("ad",""))
        yetkili  = st.text_input("Yetkili Adı",   value=firma.get("yetkili",""))
        telefon  = st.text_input("Telefon",        value=firma.get("telefon",""))
        sehirler = ["İstanbul","Ankara","İzmir","Bursa","Antalya","Adana","Konya","Diğer"]
        sehir    = st.selectbox("Şehir", sehirler,
                     index=sehirler.index(firma.get("sehir","İstanbul")))
        if st.button("💾 Kaydet", type="primary", key="firma_kaydet"):
            if not ad:
                st.error("Firma adı zorunlu.")
            else:
                st.session_state.firma_profili = {
                    **(st.session_state.firma_profili or {}),
                    "ad": ad, "yetkili": yetkili,
                    "telefon": telefon, "sehir": sehir,
                    "zorluk_carpani": 20
                }
                st.success("✅ Kaydedildi!")

    with tab2:
        st.caption("AI bu listeden fiyat hesaplar — kafasından rakam üretmez.")
        fiyatlar = st.session_state.birim_fiyatlar
        guncellenen = []
        for i, k in enumerate(fiyatlar):
            c1,c2,c3,c4 = st.columns([3,1,2,1])
            ad_k  = c1.text_input("", value=k["kalem"],  key=f"kad_{i}",  label_visibility="collapsed")
            birim = c2.selectbox("", ["m²","adet","mt","set"],
                       index=["m²","adet","mt","set"].index(k.get("birim","m²")),
                       key=f"kbr_{i}", label_visibility="collapsed")
            fiyat = c3.number_input("", value=float(k["fiyat"]), min_value=0.0,
                       step=5.0, key=f"kfiy_{i}", label_visibility="collapsed")
            sil   = c4.button("🗑️", key=f"ksil_{i}")
            if not sil:
                guncellenen.append({"kalem": ad_k, "birim": birim, "fiyat": fiyat})
        st.session_state.birim_fiyatlar = guncellened = guncellenen

        st.divider()
        st.write("**Yeni Kalem Ekle**")
        n1,n2,n3,n4 = st.columns([3,1,2,1])
        yk_ad    = n1.text_input("Kalem Adı",  key="yk_ad")
        yk_birim = n2.selectbox("Birim", ["m²","adet","mt","set"], key="yk_birim")
        yk_fiyat = n3.number_input("Fiyat", min_value=0.0, step=5.0, key="yk_fiyat")
        with n4:
            st.write(""); st.write("")
            if st.button("➕"):
                if yk_ad:
                    st.session_state.birim_fiyatlar.append(
                        {"kalem": yk_ad, "birim": yk_birim, "fiyat": yk_fiyat})
                    st.rerun()

        if st.button("💾 Fiyat Listesini Kaydet", type="primary"):
            fp = st.session_state.firma_profili or {}
            fp["birim_fiyatlar"] = st.session_state.birim_fiyatlar
            st.session_state.firma_profili = fp
            st.success("✅ Kaydedildi!")

    with tab3:
        planlar = st.session_state.odeme_planlari
        guncel  = []
        for i, p in enumerate(planlar):
            c1,c2,c3 = st.columns([2,4,1])
            pad = c1.text_input("", value=p["ad"],   key=f"pad_{i}", label_visibility="collapsed")
            ppl = c2.text_input("", value=p["plan"], key=f"ppl_{i}", label_visibility="collapsed")
            sil = c3.button("🗑️", key=f"psil_{i}")
            if not sil:
                guncel.append({"ad": pad, "plan": ppl})
        st.session_state.odeme_planlari = guncel

        st.divider()
        p1,p2,p3 = st.columns([2,4,1])
        yp_ad  = p1.text_input("Şablon Adı", key="yp_ad")
        yp_det = p2.text_input("Örn: %40 Peşinat — %60 Teslimat", key="yp_det")
        with p3:
            st.write(""); st.write("")
            if st.button("➕", key="yp_ekle"):
                if yp_ad and yp_det:
                    st.session_state.odeme_planlari.append({"ad": yp_ad, "plan": yp_det})
                    st.rerun()

        if st.button("💾 Planları Kaydet", type="primary"):
            fp = st.session_state.firma_profili or {}
            fp["odeme_planlari"] = st.session_state.odeme_planlari
            st.session_state.firma_profili = fp
            st.success("✅ Kaydedildi!")

# ══════════════════════════════════════════════════════════════════
# SAYFA: YENİ TEKLİF (5 adım)
# ══════════════════════════════════════════════════════════════════
PROJE_TURLERI = [
    "🛁 Banyo","🍳 Mutfak","🛋️ Salon","🛏️ Yatak Odası",
    "🏠 Komple Daire","🎨 Boyama","🪵 Zemin/Parke",
    "⚡ Elektrik","🔧 Tesisat","🪟 Pencere/Kapı","🏗️ Çatı/İzolasyon"
]

def sayfa_yeni_teklif():
    st.title("➕ Yeni Teklif Ver")
    adim   = st.session_state.teklif_adim
    teklif = st.session_state.aktif_teklif

    st.progress(adim / 5, text=f"Adım {adim} / 5")
    st.divider()

    # ── Adım 1: Müşteri ──
    if adim == 1:
        st.subheader("👤 Müşteri Bilgisi")
        ad  = st.text_input("Müşteri Adı Soyadı", value=teklif.get("musteri_ad",""))
        tel = st.text_input("Telefon", value=teklif.get("musteri_tel",""), placeholder="05XX XXX XX XX")
        adr = st.text_area("Adres (opsiyonel)", value=teklif.get("musteri_adres",""), height=80)
        if st.button("Devam →", type="primary", disabled=not ad):
            teklif.update({"musteri_ad": ad, "musteri_tel": tel, "musteri_adres": adr})
            st.session_state.aktif_teklif  = teklif
            st.session_state.teklif_adim   = 2
            st.rerun()

    # ── Adım 2: Proje türü ──
    elif adim == 2:
        st.subheader("🏗️ Ne Yapılacak?")
        st.caption("Birden fazla seçebilirsin")
        secili = teklif.get("proje_turu", [])
        yeni   = []
        cols   = st.columns(3)
        for i, tur in enumerate(PROJE_TURLERI):
            with cols[i % 3]:
                if st.checkbox(tur, value=tur in secili, key=f"pt_{i}"):
                    yeni.append(tur)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Geri"): st.session_state.teklif_adim = 1; st.rerun()
        with c2:
            if st.button("Devam →", type="primary", disabled=len(yeni)==0):
                teklif["proje_turu"] = yeni
                st.session_state.aktif_teklif = teklif
                st.session_state.teklif_adim  = 3
                st.rerun()

    # ── Adım 3: Mekan ──
    elif adim == 3:
        st.subheader("📐 Mekan Detayları")
        alan = st.number_input("Toplam Alan (m²)", min_value=1, max_value=2000,
                               value=teklif.get("alan", 60), step=1)
        st.caption("Net taban alanı — duvar yüzeyleri AI hesaplar.")

        durum = teklif.get("mekan_durum","Orta")
        st.write("**Mevcut Durum**")
        dc = st.columns(3)
        for label in ["İyi","Orta","Kötü"]:
            if dc[["İyi","Orta","Kötü"].index(label)].button(
                    label, type="primary" if durum==label else "secondary",
                    use_container_width=True, key=f"dur_{label}"):
                teklif["mekan_durum"] = label
                st.session_state.aktif_teklif = teklif; st.rerun()

        yas = teklif.get("bina_yasi","5-15 yıl")
        st.write("**Bina Yaşı**")
        yc = st.columns(3)
        for label in ["0-5 yıl","5-15 yıl","15+ yıl"]:
            if yc[["0-5 yıl","5-15 yıl","15+ yıl"].index(label)].button(
                    label, type="primary" if yas==label else "secondary",
                    use_container_width=True, key=f"yas_{label}"):
                teklif["bina_yasi"] = label
                st.session_state.aktif_teklif = teklif; st.rerun()

        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Geri"): st.session_state.teklif_adim = 2; st.rerun()
        with c2:
            if st.button("Devam →", type="primary"):
                teklif["alan"] = alan
                st.session_state.aktif_teklif = teklif
                st.session_state.teklif_adim  = 4; st.rerun()

    # ── Adım 4: Kalite ──
    elif adim == 4:
        st.subheader("✨ Kalite Seviyesi")
        kalite = teklif.get("kalite","Orta")
        k1, k2, k3 = st.columns(3)
        for col, label, acik in [
            (k1,"Ekonomik","Temel malzeme, standart işçilik"),
            (k2,"Orta",    "Orta segment malzeme, nitelikli işçilik"),
            (k3,"Premium", "Üst segment malzeme, usta işçilik"),
        ]:
            with col:
                st.markdown(f"**{label}**")
                st.caption(acik)
                if st.button("Seç", key=f"kal_{label}",
                             type="primary" if kalite==label else "secondary",
                             use_container_width=True):
                    teklif["kalite"] = label
                    st.session_state.aktif_teklif = teklif; st.rerun()

        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Geri"): st.session_state.teklif_adim = 3; st.rerun()
        with c2:
            if st.button("Devam →", type="primary"):
                st.session_state.teklif_adim = 5; st.rerun()

    # ── Adım 5: Süre & Ödeme ──
    elif adim == 5:
        st.subheader("📅 Süre & Ödeme")
        alan   = teklif.get("alan", 60)
        n_prj  = len(teklif.get("proje_turu",[]))
        tahmin = max(5, min(60, int(alan / 10 * max(n_prj,1) * 0.8)))
        sure   = st.number_input("Tahmini Teslim Süresi (iş günü)",
                                  1, 180, teklif.get("sure", tahmin))

        planlar   = st.session_state.odeme_planlari
        plan_idx  = st.selectbox("Ödeme Planı", range(len(planlar)),
                                  format_func=lambda i: f"{planlar[i]['ad']} — {planlar[i]['plan']}",
                                  index=teklif.get("odeme_plan_idx",0))
        ozel_not  = st.text_area("Özel Notlar (opsiyonel)",
                                  value=teklif.get("ozel_not",""),
                                  placeholder="Örn: Müşteri seramikleri kendisi alacak",
                                  height=80)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Geri"): st.session_state.teklif_adim = 4; st.rerun()
        with c2:
            if st.button("🤖 AI ile Teklif Oluştur", type="primary"):
                teklif.update({
                    "sure": sure,
                    "odeme_plan_idx": plan_idx,
                    "odeme_plani": planlar[plan_idx],
                    "ozel_not": ozel_not
                })
                st.session_state.aktif_teklif = teklif
                st.session_state.teklif_adim  = 1
                # AI kalemlerini temizle ki yeniden üretsin
                if "ai_kalemler" in st.session_state:
                    del st.session_state["ai_kalemler"]
                if "zorluk_onaylandi" in st.session_state:
                    del st.session_state["zorluk_onaylandi"]
                st.session_state.sayfa = "kalem_onay"; st.rerun()

# ══════════════════════════════════════════════════════════════════
# SAYFA: KALEM ONAY
# ══════════════════════════════════════════════════════════════════
KALITE_CARPANI = {"Ekonomik": 0.85, "Orta": 1.0, "Premium": 1.35}

def ai_kalem_olustur(teklif, birim_fiyatlar):
    client = anthropic.Anthropic(api_key=get_api_key())
    proje   = ", ".join(teklif.get("proje_turu",[]))
    alan    = teklif.get("alan", 60)
    durum   = teklif.get("mekan_durum","Orta")
    bina    = teklif.get("bina_yasi","5-15 yıl")
    kalite  = teklif.get("kalite","Orta")
    not_    = teklif.get("ozel_not","")
    fiyat_listesi = "\n".join(
        f"- {b['kalem']}: {b['fiyat']} TL/{b['birim']}" for b in birim_fiyatlar)

    prompt = f"""Sen bir tadilat teklif asistanısın. Aşağıdaki proje için iş kalemi listesi oluştur.

PROJE:
- Tür: {proje}
- Alan: {alan} m² (taban)
- Durum: {durum} | Bina yaşı: {bina}
- Kalite: {kalite}
- Not: {not_ or 'Yok'}

BİRİM FİYAT LİSTESİ:
{fiyat_listesi}

GÖREV:
1. Gerekli iş kalemlerini listele
2. Her kalem için gerçekçi miktar tahmini yap (örn: 12m² banyo tabanı → ~28m² duvar seramiği)
3. Fiyatları YALNIZCA yukarıdaki listeden al; listede yoksa birim_fiyat=0 bırak
4. ai_not alanına kısa hesaplama mantığını yaz

SADECE JSON döndür, başka hiçbir şey yazma:
[
  {{"kalem":"...", "miktar":25, "birim":"m²", "birim_fiyat":130, "ai_not":"12m² taban → 25m² duvar tahmini"}}
]"""

    msg = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2000,
        messages=[{"role":"user","content":prompt}]
    )
    text = msg.content[0].text.strip()
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"): text = text[4:]
    kalemler = json.loads(text)
    carpan   = KALITE_CARPANI.get(teklif.get("kalite","Orta"), 1.0)
    for k in kalemler:
        k["birim_fiyat"] = round(float(k.get("birim_fiyat",0)) * carpan)
        k["toplam"]      = round(k["miktar"] * k["birim_fiyat"])
        k["onaylandi"]   = True
    return kalemler

def sayfa_kalem_onay():
    st.title("🤖 AI Kalem Listesi")
    teklif        = st.session_state.aktif_teklif
    firma         = st.session_state.firma_profili or {}
    birim_fiyatlar = st.session_state.birim_fiyatlar

    # ── Zorluk çarpanı uyarısı ──
    zorluk_var = (teklif.get("mekan_durum")=="Kötü" or teklif.get("bina_yasi")=="15+ yıl")
    if zorluk_var and not st.session_state.get("zorluk_onaylandi"):
        carpan = firma.get("zorluk_carpani", 20)
        st.warning(f"⚠️ Eski bina / kötü durum tespit edildi. Birim fiyatlara **%{carpan} ek** önerilir.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"✅ Evet, %{carpan} ekle", type="primary"):
                arttirilmis = [
                    {**b, "fiyat": round(b["fiyat"] * (1 + carpan/100))}
                    for b in birim_fiyatlar
                ]
                st.session_state.birim_fiyatlar_gecici = arttirilmis
                st.session_state.zorluk_onaylandi = True
                st.rerun()
        with c2:
            if st.button("❌ Hayır, normal fiyat"):
                st.session_state.birim_fiyatlar_gecici = birim_fiyatlar
                st.session_state.zorluk_onaylandi = True
                st.rerun()
        return

    aktif_fiyatlar = st.session_state.get("birim_fiyatlar_gecici") or birim_fiyatlar

    # ── AI kalem üret (bir kez) ──
    teklif_hash = str(sorted(teklif.items()))
    if "ai_kalemler" not in st.session_state:
        with st.spinner("🤖 AI kalemler hesaplıyor..."):
            try:
                kalemler = ai_kalem_olustur(teklif, aktif_fiyatlar)
                st.session_state.ai_kalemler  = kalemler
                st.session_state.ai_teklif_hash = teklif_hash
            except Exception as e:
                st.error(f"AI hatası: {e}")
                return

    kalemler = st.session_state.ai_kalemler
    st.caption("Miktarları +/− ile ayarla, istemediğin kalemleri kaldır.")

    toplam = 0
    for i, k in enumerate(kalemler):
        c1,c2,c3,c4,c5,c6 = st.columns([3,0.6,1.2,0.6,2,0.8])
        with c1:
            st.write(f"**{k['kalem']}**")
            if k.get("ai_not"): st.caption(f"💡 {k['ai_not']}")
        with c2:
            if st.button("−", key=f"azalt_{i}"):
                k["miktar"] = max(0, k["miktar"]-1)
                k["toplam"] = k["miktar"]*k["birim_fiyat"]
                st.session_state.ai_kalemler[i]=k; st.rerun()
        with c3:
            st.metric("", f"{k['miktar']} {k['birim']}")
        with c4:
            if st.button("+", key=f"artir_{i}"):
                k["miktar"] += 1
                k["toplam"]  = k["miktar"]*k["birim_fiyat"]
                st.session_state.ai_kalemler[i]=k; st.rerun()
        with c5:
            st.write(f"{k['birim_fiyat']:,.0f} TL/{k['birim']}")
            st.write(f"**{k['miktar']*k['birim_fiyat']:,.0f} TL**")
        with c6:
            aktif = st.checkbox("", value=k.get("onaylandi",True), key=f"akt_{i}")
            k["onaylandi"] = aktif
        st.divider()
        if k["onaylandi"]:
            toplam += k["miktar"]*k["birim_fiyat"]

    st.markdown(f"## 💰 Toplam: **{toplam:,.0f} TL**")

    ca, cb, cc = st.columns(3)
    with ca:
        if st.button("← Forma Dön"):
            del st.session_state["ai_kalemler"]
            st.session_state.sayfa="yeni_teklif"; st.session_state.teklif_adim=5; st.rerun()
    with cb:
        if st.button("🔄 Yeniden Üret"):
            del st.session_state["ai_kalemler"]; st.rerun()
    with cc:
        if st.button("📄 Teklifi Oluştur →", type="primary"):
            aktif_kalemler = [k for k in kalemler if k.get("onaylandi")]
            teklif["kalemler"]     = aktif_kalemler
            teklif["toplam_tutar"] = toplam
            teklif["durum"]        = "Taslak"
            st.session_state.aktif_teklif = teklif
            st.session_state.sayfa = "onizleme"; st.rerun()

# ══════════════════════════════════════════════════════════════════
# SAYFA: ÖNİZLEME
# ══════════════════════════════════════════════════════════════════
def pdf_olustur(teklif, firma):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Table,
                                     TableStyle, Spacer, HRFlowable)
    from reportlab.lib.enums import TA_CENTER
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import io, os

    # DejaVu fontlarını kaydet (Türkçe karakter desteği)
    # Önce proje klasöründe ara, sonra sistem fontlarına bak
    base_dir = os.path.dirname(os.path.abspath(__file__))
    font_normal = os.path.join(base_dir, "DejaVuSans.ttf")
    font_bold   = os.path.join(base_dir, "DejaVuSans-Bold.ttf")
    if not os.path.exists(font_normal):
        font_normal = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        font_bold   = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if os.path.exists(font_normal):
        pdfmetrics.registerFont(TTFont("DejaVu",      font_normal))
        pdfmetrics.registerFont(TTFont("DejaVu-Bold", font_bold))
        NORMAL_FONT = "DejaVu"
        BOLD_FONT   = "DejaVu-Bold"
    else:
        NORMAL_FONT = "Helvetica"
        BOLD_FONT   = "Helvetica-Bold"

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
          rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

    styles  = getSampleStyleSheet()
    MAVI    = colors.HexColor("#1E3A5F")
    ACIK    = colors.HexColor("#EBF3FB")
    GRI     = colors.HexColor("#666666")
    elems   = []

    def stil(name, parent="Normal", **kw):
        return ParagraphStyle(name, parent=styles[parent], fontName=NORMAL_FONT, **kw)

    elems.append(Paragraph(firma.get("ad","Firma"), stil("b",fontSize=20,textColor=MAVI,spaceAfter=4)))
    elems.append(Paragraph(
        f"{firma.get('yetkili','')} | {firma.get('telefon','')} | {firma.get('sehir','')}",
        stil("s",fontSize=10,textColor=GRI)))
    elems.append(HRFlowable(width="100%",thickness=2,color=MAVI,spaceAfter=12))

    tarih     = datetime.now().strftime("%d.%m.%Y")
    teklif_no = teklif.get("id","001")
    info = [
        ["MÜŞTERİ",teklif.get("musteri_ad",""),"TARİH",tarih],
        ["TELEFON", teklif.get("musteri_tel",""),"TEKLİF NO",f"#{teklif_no}"],
        ["ADRES",   teklif.get("musteri_adres","-"),"TESLİMAT",f"{teklif.get('sure','-')} iş günü"],
    ]
    it = Table(info, colWidths=[3*cm,7*cm,3*cm,5*cm])
    it.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,-1),NORMAL_FONT),("FONTSIZE",(0,0),(-1,-1),9),
        ("FONTNAME",(0,0),(0,-1),BOLD_FONT),("FONTNAME",(2,0),(2,-1),BOLD_FONT),
        ("TEXTCOLOR",(0,0),(0,-1),MAVI),("TEXTCOLOR",(2,0),(2,-1),MAVI),
        ("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),
    ]))
    elems += [it, Spacer(1,12)]
    elems.append(Paragraph("İŞ KALEMLERİ",
        stil("kh",fontSize=12,textColor=MAVI,spaceBefore=16,spaceAfter=8)))

    header  = [["#","Kalem","Miktar","Birim Fiyat","Toplam"]]
    rows    = [[str(i+1), k["kalem"], f"{k['miktar']} {k['birim']}",
                f"{k['birim_fiyat']:,.0f} TL", f"{k['miktar']*k['birim_fiyat']:,.0f} TL"]
               for i,k in enumerate(teklif.get("kalemler",[]))]
    kt = Table(header+rows, colWidths=[1*cm,8.5*cm,2.5*cm,3*cm,3*cm])
    kt.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),MAVI),("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),BOLD_FONT),("FONTSIZE",(0,0),(-1,0),9),
        ("ALIGN",(0,0),(-1,0),"CENTER"),
        ("FONTNAME",(0,1),(-1,-1),NORMAL_FONT),("FONTSIZE",(0,1),(-1,-1),9),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,ACIK]),
        ("ALIGN",(0,1),(0,-1),"CENTER"),("ALIGN",(2,1),(-1,-1),"RIGHT"),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(1,0),(1,-1),8),
        ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#CCCCCC")),
    ]))
    elems.append(kt)

    toplam = teklif.get("toplam_tutar",0)
    tt = Table([["","","","TOPLAM",f"{toplam:,.0f} TL"]],
               colWidths=[1*cm,8.5*cm,2.5*cm,3*cm,3*cm])
    tt.setStyle(TableStyle([
        ("BACKGROUND",(3,0),(-1,0),MAVI),("TEXTCOLOR",(3,0),(-1,0),colors.white),
        ("FONTNAME",(3,0),(-1,0),BOLD_FONT),("FONTSIZE",(3,0),(-1,0),11),
        ("ALIGN",(3,0),(-1,0),"RIGHT"),
        ("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8),
    ]))
    elems += [tt, Spacer(1,16)]

    odeme = teklif.get("odeme_plani",{})
    if odeme:
        elems.append(HRFlowable(width="100%",thickness=0.5,color=GRI))
        elems.append(Spacer(1,8))
        elems.append(Paragraph(f"<b>ÖDEME PLANI:</b> {odeme.get('plan','')}",
                     stil("op",fontSize=10,textColor=MAVI)))
        elems.append(Spacer(1,8))
    if teklif.get("ozel_not"):
        elems.append(Paragraph(f"<b>NOT:</b> {teklif['ozel_not']}",
                     stil("nt",fontSize=9,textColor=GRI)))
        elems.append(Spacer(1,12))

    elems.append(HRFlowable(width="100%",thickness=0.5,color=GRI))
    elems.append(Spacer(1,20))
    imza = Table([
        ["MÜŞTERİ","","FİRMA"],
        [teklif.get("musteri_ad",""),"",firma.get("ad","")],
        ["","",""],
        ["İmza / Tarih: _______________","","İmza / Tarih: _______________"],
    ], colWidths=[8*cm,2*cm,8*cm])
    imza.setStyle(TableStyle([
        ("FONTNAME",(0,0),(-1,-1),NORMAL_FONT),("FONTSIZE",(0,0),(-1,-1),9),
        ("FONTNAME",(0,0),(0,0),BOLD_FONT),("FONTNAME",(2,0),(2,0),BOLD_FONT),
        ("TEXTCOLOR",(0,0),(-1,0),MAVI),("ALIGN",(2,0),(2,-1),"RIGHT"),
        ("TOPPADDING",(0,0),(-1,-1),4),
    ]))
    elems += [imza, Spacer(1,20)]
    elems.append(Paragraph("Bu teklif müşteri tarafından imzalandığında sözleşme niteliği taşır.",
                 stil("ft",fontSize=8,textColor=GRI,alignment=TA_CENTER)))

    doc.build(elems)
    buffer.seek(0)
    return buffer.getvalue()

def sayfa_onizleme():
    st.title("📄 Teklif Önizleme")
    teklif = st.session_state.aktif_teklif
    firma  = st.session_state.firma_profili or {"ad":"Firma","telefon":"","sehir":""}

    if not teklif:
        st.error("Teklif bulunamadı."); return

    kalemler = teklif.get("kalemler",[])
    toplam   = teklif.get("toplam_tutar",0)
    odeme    = teklif.get("odeme_plani",{})

    st.markdown(f"""
---
### {firma['ad']}
**{firma.get('yetkili','')}** | {firma.get('telefon','')} | {firma.get('sehir','')}
---
**MÜŞTERİ:** {teklif.get('musteri_ad','')} — {teklif.get('musteri_tel','')}  
**ADRES:** {teklif.get('musteri_adres','-')}  
**TARİH:** {datetime.now().strftime('%d.%m.%Y')} | **TESLİMAT:** {teklif.get('sure','-')} iş günü
---""")

    c1,c2,c3,c4 = st.columns([4,2,2,2])
    for h in ["Kalem","Miktar","Birim Fiyat","Toplam"]:
        [c1,c2,c3,c4][["Kalem","Miktar","Birim Fiyat","Toplam"].index(h)].markdown(f"**{h}**")
    st.divider()
    for k in kalemler:
        a,b,c,d = st.columns([4,2,2,2])
        a.write(k["kalem"])
        b.write(f"{k['miktar']} {k['birim']}")
        c.write(f"{k['birim_fiyat']:,.0f} TL")
        d.write(f"{k['miktar']*k['birim_fiyat']:,.0f} TL")
    st.divider()
    st.markdown(f"### TOPLAM: **{toplam:,.0f} TL**")
    if odeme: st.markdown(f"**ÖDEME PLANI:** {odeme.get('plan','-')}")
    if teklif.get("ozel_not"): st.markdown(f"**NOT:** {teklif['ozel_not']}")
    st.markdown("---")

    ca, cb, cc = st.columns(3)
    with ca:
        if st.button("← Kalemlere Dön"):
            st.session_state.sayfa="kalem_onay"; st.rerun()
    with cb:
        try:
            pdf_bytes = pdf_olustur(teklif, firma)
            ad = teklif.get("musteri_ad","teklif").replace(" ","_")
            st.download_button("⬇️ PDF İndir", pdf_bytes,
                file_name=f"teklif_{ad}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf", type="primary", use_container_width=True)
        except Exception as e:
            st.error(f"PDF hatası: {e}")
    with cc:
        if st.button("💾 Kaydet", use_container_width=True):
            if not teklif.get("id"):
                teklif["id"]    = str(uuid.uuid4())[:8]
                teklif["tarih"] = datetime.now().strftime("%d.%m.%Y")
                teklif["durum"] = "Taslak"
                st.session_state.teklifler.append(teklif.copy())
            st.success("✅ Kaydedildi!")
            if st.button("📋 Tekliflerime Git"):
                st.session_state.sayfa="teklifler"; st.rerun()

# ══════════════════════════════════════════════════════════════════
# SAYFA: TEKLİFLER
# ══════════════════════════════════════════════════════════════════
DURUM_RENK = {"Taslak":"🟡","Gönderildi":"🔵","İncelendi":"🟠","Onaylandı":"🟢","Reddedildi":"🔴"}
DURUMLAR   = ["Taslak","Gönderildi","İncelendi","Onaylandı","Reddedildi"]

def sayfa_teklifler():
    st.title("📋 Tekliflerim")
    teklifler = st.session_state.teklifler

    if not teklifler:
        st.info("Henüz teklif yok.")
        if st.button("➕ Yeni Teklif Ver", type="primary"):
            st.session_state.sayfa="yeni_teklif"; st.session_state.aktif_teklif={}
            st.session_state.teklif_adim=1; st.rerun()
        return

    filtre = st.selectbox("Durum", ["Tümü"]+DURUMLAR)
    liste  = teklifler if filtre=="Tümü" else [t for t in teklifler if t.get("durum")==filtre]
    st.write(f"**{len(liste)} teklif**")
    st.divider()

    for i, t in enumerate(reversed(liste)):
        gercek_i = len(teklifler)-1-i
        proje  = ", ".join(t.get("proje_turu",[]))
        durum  = t.get("durum","Taslak")
        with st.expander(
            f"{DURUM_RENK.get(durum,'⚪')} {t.get('musteri_ad','-')} — "
            f"{proje[:40]} — {t.get('toplam_tutar',0):,.0f} ₺ — {t.get('tarih','')}"
        ):
            c1,c2 = st.columns(2)
            with c1:
                st.write(f"**Müşteri:** {t.get('musteri_ad','-')}")
                st.write(f"**Telefon:** {t.get('musteri_tel','-')}")
                st.write(f"**Alan:** {t.get('alan','-')} m²  |  **Kalite:** {t.get('kalite','-')}")
            with c2:
                st.write(f"**Süre:** {t.get('sure','-')} iş günü")
                st.write(f"**Ödeme:** {t.get('odeme_plani',{}).get('plan','-')}")
                st.write(f"**Toplam:** {t.get('toplam_tutar',0):,.0f} ₺  |  **Tarih:** {t.get('tarih','-')}")

            yeni_durum = st.selectbox("Durum", DURUMLAR,
                           index=DURUMLAR.index(durum), key=f"ds_{i}")
            if yeni_durum != durum:
                st.session_state.teklifler[gercek_i]["durum"] = yeni_durum; st.rerun()

            tel = t.get("musteri_tel","").replace(" ","").replace("-","")
            if tel:
                firma = st.session_state.firma_profili or {}
                msg   = (f"Merhaba {t.get('musteri_ad','')}, {firma.get('ad','Firmamız')} olarak "
                         f"hazırladığımız teklifiniz için iletişime geçiyoruz. "
                         f"Toplam tutar: {t.get('toplam_tutar',0):,.0f} TL, "
                         f"teslim süresi: {t.get('sure','-')} iş günü. İyi günler!")
                wa = f"https://wa.me/90{tel.lstrip('0')}?text={urllib.parse.quote(msg)}"
                st.link_button("📱 WhatsApp'tan Gönder", wa)

# ══════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════
sayfa = st.session_state.sayfa
if   sayfa == "ana_sayfa":   sayfa_ana()
elif sayfa == "ayarlar":     sayfa_ayarlar()
elif sayfa == "yeni_teklif": sayfa_yeni_teklif()
elif sayfa == "kalem_onay":  sayfa_kalem_onay()
elif sayfa == "onizleme":    sayfa_onizleme()
elif sayfa == "teklifler":   sayfa_teklifler()
