# ECUWorkbench yol haritası (T-0063)

Bu belge sahip onaylı tasarım paketine karşı planlanan mimariyi ve kabul sınırlarını kaydeder. Codex `src/` ve `tests/` sahibidir; bu belge bunları değiştirmez, yalnızca karşılarında planlanır. Kanıtlanmamış hiçbir "çalışıyor" veya "benzersiz" iddiası içermez.

## 1. Kapsam kararı ve ekosistemdeki yer

`docs/ECOSYSTEM_RESEARCH.md` bulgusu: rusEFI'nin zaten çalışan `mcp_ecu` (canlı veri, Lua, firmware güncelleme) ve `mcp_can` (salt okunur CAN) araçları var; OpenTune ve ECU Explorer benzer "AI + tuning + MCP" alanında tasarım/README seviyesinde örtüşüyor. Bu nedenle ECUWorkbench:

- Yeni bir firmware/transport/CAN yığını **yazmaz**; v0.1 tamamen çevrimdışı dosya incelemesidir.
- "İlk ECU MCP" veya "benzersiz" iddiası **kullanılmaz**; seçilen kapsam farkı markalar arası çevrimdışı artifact incelemesi + sürüm/INI uyumluluğu + kaynak hash'ine bağlı, insanın onayladığı değişiklik taslaklarıdır (ECOSYSTEM_RESEARCH.md §"Benzer çalışmalar ve kapsam farkı").
- rusEFI ile ilişki: ileride adaptör/birlikte çalışabilirlik değerlendirilir; mevcut `mcp_ecu`/`mcp_can` klonlanmaz veya yeniden uygulanmaz.

## 2. Topoloji (metin diyagramı)

```
Sahip / Claude veya Codex istemcisi (stdio MCP client)
        |
        v
+-------------------------------------------+
| ECUWorkbench MCP sunucusu (FastMCP, stdio) |
| src/ecuworkbench/server.py                 |
|   tools: capabilities, inspect_tune,       |
|          compare_tunes, summarize_log      |
+-------------------------------------------+
        |
        v  (yalnız dosya okuma; ağ/seri/CAN yok)
+-------------------------------------------+
| src/ecuworkbench/artifacts.py              |
|   - ECU_WORKBENCH_ROOT sınırı              |
|   - boyut/sayı üst sınırları               |
|   - defusedxml (DTD/entity/external kapalı)|
|   - sha256 kaynak izi                      |
+-------------------------------------------+
        |
        v
+-------------------------------------------+
| ECU_WORKBENCH_ROOT altında kullanıcı       |
| dosyaları (.msq, .csv, gelecekte .tsv/.ini)|
+-------------------------------------------+
        |
   (yok; yalnız gelecekte, ayrı onayla)
        v
+-------------------------------------------+
| ECU donanımı / simülatör (seri, CAN)       |
| v0.1'de erişilmiyor                        |
+-------------------------------------------+
```

Not: sunucu ile ECU donanımı arasında bugün hiçbir bağlantı yok; alt kutu yalnız gelecekteki milestone'ların nereye bağlanacağını gösterir.

## 3. v0.1 gerçek kabul kapsamı (mevcut `src/ecuworkbench` koduna göre)

Aşağıdakiler `artifacts.py`/`server.py` içinde uygulanmış görünüyor; bu plan bunları **kod okuyarak** tespit etmiştir, ayrı bir test çalıştırılarak doğrulanmamıştır (bkz. §7 kanıt yolları ve durum).

- `capabilities()`: desteklenen biçimler (`msq`, `csv`), desteklenmeyenler (native MLG, native MaxxECU tune/log, seri, CAN, flashing, yazma), sabit limitler, `external_requests=False`, `local_inference=False`.
- `inspect_tune(path)`: yalnız `.msq`, DTD/entity/external kapalı XML ayrıştırma, tek/tutarlı firmware signature zorunluluğu, sayfa/isim başına tekil sabitler, ham metin değer + birim, `interpretation` alanında kalibrasyon doğrulaması yapılmadığı açık uyarısı.
- `compare_tunes(left, right)`: yalnız eşleşen firmware signature, birim uyuşmazlığında hata (sessiz dönüşüm yok), sayfa+isim anahtarına göre eklenen/silinen/değişen liste, `before`/`after` ham değerler.
- `summarize_log(path, units)`: yalnız `.csv`, UTF-8 zorunlu, başlık satırı tekil/boş olmayan, çağıranın açıkça verdiği birimler dışında birim `unknown`, sayısal/eksik/sayısal-olmayan/sonlu-olmayan sayaçları, min/max/mean; zaman damgası veya kalibrasyon doğruluğu çıkarımı yok.
- Tüm okumalar `ECU_WORKBENCH_ROOT` içine `resolve(strict=True)` ile sabitlenmiş, 10 MiB/4096 sabit/512 sütun/100000 satır üst sınırlı, kaynak `sha256` ile iz bırakılmış.

v0.1 kabul ölçütü (test edilecek, henüz doğrulanmadı): sentetik `.msq` fixture'ı için `inspect_tune` ve `compare_tunes`'ın belirtilen hata/başarı yollarını üretmesi; sentetik `.csv` için `summarize_log`'un sayaç ve istatistikleri doğru üretmesi; `ECU_WORKBENCH_ROOT` dışına, sembolik bağlantı hedef değişikliğine ve boyut/sayı sınırlarını aşan girdilere karşı reddin `tests/` içinde kanıtlanması.

## 4. Sonraki adım: MaxxECU XML/TSV ve sürüm sözleşmesi

MaxxECU biçimleri (`docs/ECOSYSTEM_RESEARCH.md` §MaxxECU): `.MaxxECU-save` XML, `.MaxxECU-log`/`.maxxlog` TAB ayrımlı, CSV ihracı, log+tune içeren zip. Kapalı biçim tahmin edilerek yazılmaz; yalnız kullanıcının dışa aktardığı dosyalar okunur.

Planlanan adaptör sözleşmesi (`ECOSYSTEM_RESEARCH.md` §"Adapter kabul sözleşmesi" ile uyumlu):

1. Üretici + ECU/board modeli + firmware signature/sürüm alanları `inspect_tune`'daki gibi ayrı, zorunlu ve boş bırakılamaz olacak; bilinmeyen sürüm "bilinen" gibi doldurulmayacak.
2. `.MaxxECU-save` XML kök etiketi ve alan şeması ayrı bir okuyucu (`inspect_maxxecu_tune` benzeri, adı Codex'e bırakılır) ile ele alınacak; mevcut `.msq` okuyucusu değiştirilmeyecek (biçimler karıştırılmaz).
3. `.MaxxECU-log`/`.maxxlog` TAB ayrımlı biçimi CSV özetleyiciden ayrı bir ayrıştırıcı gerektirir; sütun/birim eşlemesi yalnız dosyanın kendi başlığından veya kullanıcının verdiği eşlemeden gelir, tahmini birim eklenmez.
4. MaxxECU native tune için üreticinin sürüm/parametre şeması ve kullanıcı ihracı doğrulanır. MaxxECU'nun TunerStudio INI kullandığı bu araştırmada gösterilmedi; böyle bir INI koşulu icat edilmez. INI/signature eşleştirmesi MSQ/TunerStudio ekosistemi için ayrı adaptördür. Sürüm veya ölçek bilinmiyorsa anlamı uydurulmaz.
5. CAN DBC (MaxxECU'nun yayınladığı) yalnız kullanıcının kendi indirdiği ve lisansını doğruladığı dosya olarak kabul edilir; ECUWorkbench DBC'yi paket içine gömmez veya otomatik indirmez.
6. Bu adım da v0.1 gibi çevrimdışı ve salt okunur kalır; CAN/seri iletişim eklenmez.

Kabul ölçütü: belgelenmiş MaxxECU XML/TSV şemasına dayalı fixture'larla sürüm, dosya bütünlüğü ve birim/parametre eşlemesi hatalarının açıkça durdurulması. Ayrı MSQ/INI paketi signature uyuşmazlığını test eder.

## 5. Reviewed change proposal (tune patch) sözleşmesi

`constitution.md` madde 9 ve `ECOSYSTEM_RESEARCH.md` §"Adapter kabul sözleşmesi" madde 4 uyarınca, ilerideki herhangi bir "önerilen değişiklik" özelliği şu alanları taşımadan üretilmez:

- `baseline_sha256`: değişikliğin dayandığı kaynak dosyanın `_read()` ile üretilen hash'i.
- `target`: sayfa + sabit adı (mevcut `compare_tunes` anahtarlama şemasıyla aynı).
- `previous_value` ve `unit`: kaynaktan okunan ham değer, dönüştürülmeden.
- `proposed_value` ve gerekçe metni: yalnız insan tarafından girilir; otomatik/öğrenilmiş sayısal öneri **yok**.
- Çıktı her zaman **yeni bir dosya**dır; mevcut tune dosyası yerinde değiştirilmez, ECU'ya yazılmaz.

Bu özellik v0.1'de yoktur; yalnız gelecekteki bir milestone için sözleşme burada sabitlenmiştir.

## 6. Simülatör ve donanım sırası

- rusEFI'nin var olan simülatörü (ör. `rusefi_simulator`/native sim hedefleri) yeniden kullanılacak adaydır; ECUWorkbench kendi ECU firmware simülatörünü **yazmaz**.
- Sıra: (a) sentetik dosya fixture'ları → (b) rusEFI simülatör çıktısı ile üretilmiş gerçekçi ama gerçek araç olmayan dosyalar → (c) sahibin kendi aracından/ECU donanımından dışa aktarılmış dosyalar, bench'te doğrulanmış → (d) yalnız bundan sonra, ayrı onayla, canlı/write yollar değerlendirilir.
- Canlı ECU'ya bağlı hiçbir adım, bench doğrulaması ve ayrı sahip onayı olmadan atlanmaz.

## 7. Lisans/iş akışı ayrımı

- **Kodlama iş akışı:** bu depoda bağımsız yazılan kod MIT'tir. Yukarı akış kodu/donanımı alınırsa ilgili bileşenin GPL/CERN-OHL koşulları ayrıca uygulanır; bir protokolü kullanan her bağımsız adaptörün otomatik olarak aynı lisansa tabi olduğu iddia edilmez.
- **Kapalı/destek belgeleri** (MSExtra kullanım koşulları, MaxxECU webhelp/DBC, vendor PDF'leri): bunlar OSS değildir; ECUWorkbench bunları kopyalamaz, yalnız kullanıcının kendi dışa aktardığı dosyaları okur ve kaynağa referans verir.
- Sentetik örnekler dışında hiçbir üretici firmware/INI/DBC veya özel müşteri tune/log dosyası bu depoya konmaz (`ECOSYSTEM_RESEARCH.md` madde 6).

## 8. Adaptör matrisi

| Ekosistem | v0.1 durumu | Sonraki adım | Lisans notu |
| --- | --- | --- | --- |
| MSExtra/MegaSquirt MSQ | Uygulanmış (`inspect_tune`, `compare_tunes`) | Ek MS INI sürüm eşleştirmesi değerlendirilecek | MS2 belgesi OSS değil; güncel MS3 lisansı doğrulanmadı |
| MaxxECU XML tune | Yok | §4 planı | Format erişimi var, firmware OSS lisansı doğrulanmadı |
| MaxxECU TSV log | Yok | §4 planı | Aynı yukarıdaki gibi |
| TunerStudio MSQ/INI eşleşmesi | Yok | Ayrı MSQ signature/INI sözleşmesi; MaxxECU INI varsayımı yok | Kullanıcının lisanslı dosyaları |
| CSV log (jenerik) | Uygulanmış (`summarize_log`) | Ek zaman damgası sütunu tespiti değerlendirilecek | Vendor bağımsız, kullanıcı dosyası |
| rusEFI (mcp_ecu/mcp_can) | Yok, klonlanmayacak | İleride adaptör/birlikte çalışabilirlik araştırması | GPLv3 (`license.txt`) |
| Speeduino | Yok | Araştırma adayı | Firmware GPLv2, donanım CERN-OHL-S v2 |
| FOME | Yok | Lisans/sürüm doğrulanmadan adapter iddia edilmez | Bu turda doğrulanmadı |

## 9. Milestone kabul özeti

| Milestone | Kapsam | Kabul kanıtı |
| --- | --- | --- |
| M0 (mevcut) | `.msq` inceleme/karşılaştırma, CSV özet, `capabilities` | 38 sentetik test + gerçek stdio MCP; bağımsız kabul §13 |
| M1 | MaxxECU XML/TSV sürüm şeması ve ayrı MSQ/INI okuyucu | §4 sürüm/birim/şema red yollarının kanıtı |
| M2 | Reviewed change proposal (baseline hash + eski değer + birim + öneri metni, yalnız yeni dosya) | §5 sözleşmesine uyan örnek üretim + red yollarının testi |
| M3 | rusEFI simülatör çıktısıyla gerçekçi fixture doğrulama | Simülatör kurulum kanıtı + üretilen dosya + testten geçme kaydı |
| M4 | Bench'te gerçek donanımdan dışa aktarılmış dosyalarla doğrulama | Sahip onayı + bench kanıt notu; bu belge canlı ECU erişimi eklemez |

## 10. Kanıt yolları

- Kod: `src/ecuworkbench/server.py`, `src/ecuworkbench/artifacts.py` (Codex sahipliğinde, mevcut).
- Mevcut testler: `tests/test_artifacts.py`, `tests/test_mcp.py`, `tests/test_mcp_transport.py`; sentetik fixture'lar test içinde oluşturulur.
- Bağımsız doğrulama çıktısı: `reports/verification.json`; Claude planlama koşusu test çalıştırmadı, Codex kabul koşusu çalıştırdı.
- MaxxECU/M1 fixture'ları: `tests/fixtures/maxxecu/*` (planlanan yol; henüz yok).

## 11. Doğrulama sınırları

- Claude planı yazarken test çalıştırmadı. Sonraki bağımsız kabul M0 için 38 testi ve gerçek MCP taşımasını doğruladı; §13 ve rapora bak.
- Resmî SDK stdio çağrısı geçti; Claude bağlantısı Connected, Codex kaydı enabled. Bir modelin bu araçlarla gerçek ECU mühendisliği yaptığı ölçülmedi; yeni oturum gerekir.
- rusEFI simülatörünün bu makinede kurulup çalıştığı doğrulanmadı; §6 yalnız plan.
- Gerçek araç kalibrasyonu ve simülatör/bench kapıları ölçülmedi; dosya/taşıma testleri bu kapıların yerine geçmez.

## 12. Sahibe sorular (araç/donanım/tune-log seçimi öncesi)

1. İlk gerçek doğrulama için hangi araç/motor ve hangi MaxxECU donanım kuşağı (GEN1 MINI/STREET/SPORT/RACE/RACE H2O/PRO veya GEN2) kullanılacak? GEN1'de Lua script yok; kapsam buna göre daraltılmalı.
2. Firmware/ECU yazılım sürümü tam olarak hangisi (MS3 için de: hangi build/README/LICENSE ekranı görüldü)? Sürüm doğrulanmadan INI/signature eşleştirmesi yapılamaz.
3. M1 için MaxxECU `.MaxxECU-save` XML ve `.MaxxECU-log`/`.maxxlog` kullanıcı ihracı hangisi? TunerStudio INI yalnız ilgili MSQ ekosistemi için istenir. Özel araç verileri kamu deposuna girmez.
4. rusEFI simülatörünü M3 için kurma yetkisi ve hangi sürüm/commit referans alınacak?
5. Reviewed change proposal (M2) için önerilecek örnek parametrelerin gerçek bir motor bağlamı mı yoksa tamamen sentetik mi olması isteniyor; gerekçe metnini kim (hangi rol) onaylayacak?

Bu belge planlama ve sınır kaydıdır; sahibi yeni projenin bu başlangıç uygulamasını, bağımlılıklarını ve yayınını zaten istedi. Sonraki canlı donanım işleri ayrıca tanımlanır.

## 13. Bağımsız kabul güncellemesi

Claude planı test çalıştırmadan yazdı; yukarıdaki oturum notları bu sınırı
korur. Sonrasında Codex implementasyon koşusu 38 testi geçti; stdio SDK
istemcisi initialize/list_tools/call_tool ile dört aracı ve gerçek sentetik
MSQ okumasını doğruladı. Ayrıntı `HANDOVER.md` ve `reports/verification.json`.
Bu kabul sentetik dosya/MCP paketine aittir; gerçek araç, MaxxECU native
adapter ve kalibrasyon doğruluğu hâlâ açık.
