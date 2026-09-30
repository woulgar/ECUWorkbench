# ECU ekosistemi ve araç kapsamı araştırması

İnceleme tarihi: 2026-09-30. Bu kayıt kamuya açık birincil kaynakları değerlendirir; gerçek ECU bağlantısı, firmware derlemesi, model çıkarımı veya protokol uyumluluk testi yapılmadı. Lisans sınıflandırması belirtilen belge/sürüm içindir; bütün bir üreticinin ürünlerine genellenmez.

## Üreticiler ve erişilebilir entegrasyon yüzeyleri

| Ekosistem | Doğrulanan yüzey | Lisans / sınır | ECUWorkbench için öneri | Kanıt güveni |
| --- | --- | --- | --- | --- |
| MSExtra / MegaSquirt | MS2/Extra 3.4 referansı firmware ve INI kullanım koşullarını gösteriyor; resmî MS3 1.3.2 duyurusu kaynak dağıtımında README/LICENSE okunmasını istiyor | MS2/Extra belgesi ürünü açık kaynak olarak tanımlamıyor; resmî B&G donanımına bağlı kullanım koşulları var. Kaynağın görülebilmesi genel OSS izni değildir. Güncel tüm MS3 sürümlerinin lisansı bu incelemede doğrulanmadı | Kullanıcının sağladığı tune/log/INI dosyalarının salt okunur analizi; kaynak veya firmware paketi yeniden dağıtma. INI/tune signature eşleşmesini ayrı kontrol et | MS2 belge içeriği yüksek; güncel MS3 lisansı açık |
| MaxxECU | `.MaxxECU-save` XML; `.MaxxECU-log` / `.maxxlog` tab ayrımlı; CSV ihracı; zip-log içinde log ve tune. Resmî CAN 1.2/1.3 tanımları ve DBC indirme duyurusu | İncelenen üretici sayfalarında açık firmware deposu veya firmware OSS lisansı doğrulanmadı. Doküman ve DBC erişimi yeniden dağıtım izni değildir | Önce kullanıcının dışa aktardığı XML/TSV/CSV dosyaları; sürüm, kanal birimi ve CAN tanımı birlikte tutulur. Kapalı formatı tahminle yazma | Dosya biçimleri yüksek; tune parametrelerinin bütün sürümlerde anlamı açık |
| MaxxECU Lua | GEN2 ECU üzerinde CAN, sanal giriş, çıkış ve canlı değerler için kullanıcı scriptleri | Resmî belge GEN1 MINI/STREET/SPORT/RACE/RACE H2O/PRO üzerinde bu script özelliğinin olmadığını açıkça söylüyor | Script örneğini yalnız donanım kuşağı doğrulanınca taslak olarak üret; MINI için destek iddia etme. Canlı çıkış kontrolü ilk MVP kapsamı değildir | Donanım kısıtı yüksek |
| rusEFI | Mevcut `mcp_ecu`: canlı veri, Lua, engine sniffer, log ve firmware güncelleme; `mcp_can`: salt okunur CAN yakalama. ECU signature hash ile eşleşen INI gerekli | Resmî `license.txt` GPLv3 metni ve ek kullanım bildirimleri içerir; kopyalanacak bileşenin kendi lisansı ayrıca kontrol edilir | Yeni bir rusEFI protokolü/MCP klonu yazma; ileride mevcut sunucuya adaptör. İlk paket çevrimdışı dosya ve INI uyumluluğu | Mevcut MCP ve signature gereği yüksek; bu makinede çalışma doğrulanmadı |
| Speeduino | Resmî firmware ve ayrı resmî donanım depoları, TunerStudio yapılandırma ekosistemi | Firmware `LICENSE`: GPLv2. Donanım README: CERN-OHL-S v2. Donanımı genel CC-BY-SA diye etiketlemek doğru değil | Açık firmwareye erişim, her tune/log biçiminin veya her kartın desteklendiği anlamına gelmez. Board/firmware/INI kimliğini adapter sözleşmesine koy | İncelenen ana depo lisansları yüksek; kart bazlı uyum ölçülmedi |
| FOME | Free Open Motorsports ECU deposu mevcut | Bu turda doğru lisans dosyası/sürümü doğrulanmadı; denenen raw yollar 404 verdi | Araştırma adayı; lisans ve dosya sözleşmesi doğrulanmadan hazır adapter olarak gösterme | Depo varlığı yüksek; lisans ve entegrasyon açık |

## Benzer çalışmalar ve kapsam farkı

| Çalışma | Kaynakta görülen kapsam | Bizim kararımız / doğrulama sınırı |
| --- | --- | --- |
| rusEFI MCP | ECU ve CAN erişimi zaten uygulanmış ekosistem | “İlk ECU MCP” iddiası kullanılmaz; vendor-native araçla çoğaltma yerine birlikte çalışabilirlik araştırılır |
| OpenTune | AI tuning/analysis tasarım belgesi deterministik araç çekirdeği, advisory öneriler ve MCP katmanı öngörüyor | Tasarım belgesi çalışan bütün özelliklerin kanıtı değildir. Reviewable patch yaklaşımı yalnız bize ait veya yeni bir fikir diye sunulmaz |
| ECU Explorer | Mitsubishi/Subaru ROM analizi, telemetry, calibration ve LLM-ready MCP araçları tarif ediliyor | Gerçek platform/transport destek matrisi sürüme bağlı; depo README'si bizim donanımda doğrulama değildir |
| OpenECU Alliance | ECU log adapterları, canonical kanal kimlikleri ve public API tanımlayan açık standardizasyon çalışması | Kanal adlarını standartlaştırma sıfırdan icat edilmez. Spec/lisans/sürüm eşleşmesi değerlendirilir; başlangıçta uzaktan adapter indirme zorunluluğu yok |

ECUWorkbench için seçilen başlangıç kapsamı: **markalar arası çevrimdışı artifact incelemesi, sürüm/INI uyumluluğu ve kaynak hashine bağlı, insanın inceleyebileceği değişiklik taslakları**. Bu bir ürün kapsamı kararıdır; piyasada benzersiz olduğu kanıtlanmış değildir. Yeni ECU firmware, kapalı vendor yazma protokolü veya çalışan araçta otomatik tuning ilk pakete dahil değildir.

## Adapter kabul sözleşmesi

1. Üretici, ECU/board modeli, firmware signature/sürümü, format ve dosya hashleri ayrı alanlarda tutulur. Bilinmeyen sürüm bilinen diye doldurulmaz.
2. Kaynak dosya değişmeden okunur; birimler ve kanal adları özgün haliyle korunur. Normalleştirme varsa açık mapping ve sürümü gösterilir.
3. Parse edilebilen dosya, o ECU'ya güvenle geri yazılabilen dosya demek değildir. İnceleme raporu bu iki kapıyı ayırır.
4. Tune patch, baseline hash + hedef parameter yolu + önceki değer + önerilen değer + gerekçe taşır. Başka baseline üzerinde sessiz uygulanmaz.
5. Bilinmeyen parametre, eksik ölçek/birim veya uyumsuz signature olduğunda değerlendirme durur; rastgele varsayılan veya otomatik firmware dönüşümü yapılmaz.
6. Yayınlanacak örnekler sentetiktir. Üretici firmware/INI/DBC ve özel müşteri tune dosyaları açık lisans doğrulanmadan pakete konmaz.

## Birincil kaynaklar

- [MS2/Extra 3.4 TunerStudio referansı, firmware license ekranı](https://www.msextra.com/doc/pdf/Megasquirt2_TunerStudio_MS_Lite_Reference-3.4.pdf).
- [Resmî MS3 1.3.2 source duyurusu](https://www.msextra.com/forums/viewtopic.php?t=55011).
- [MaxxECU dosya biçimleri](https://maxxecu.com/webhelp/mtune-file_formats.html).
- [MaxxECU default CAN protocol sürümleri](https://www.maxxecu.com/webhelp/can-default_maxxecu_protocol.html).
- [MaxxECU GEN2 Lua kullanıcı scriptleri](https://www.maxxecu.com/webhelp/advanced-lua_user_scripts.html).
- [MaxxECU CAN analyzer ve ihracı](https://www.maxxecu.com/webhelp/settings-can-tools-analyzer.html).
- [rusEFI resmî MCP rehberi](https://github.com/rusefi/rusefi/blob/master/README-mcp.md).
- [rusEFI lisans dosyası](https://github.com/rusefi/rusefi/blob/master/license.txt).
- [Speeduino firmware lisansı](https://github.com/speeduino/speeduino/blob/master/LICENSE).
- [Speeduino resmî donanım lisans açıklaması](https://github.com/speeduino/Hardware/blob/master/README.md).
- [FOME firmware deposu](https://github.com/FOME-Tech/fome-fw).
- [OpenTune AI/MCP tasarım belgesi](https://github.com/d0pawlus/OpenTune/blob/main/docs/superpowers/specs/2026-06-21-ai-tuning-and-analysis-design.md).
- [ECU Explorer README](https://github.com/colecrouter/ecu-explorer/blob/main/README.md).
- [OpenECU Alliance başlangıç rehberi](https://oecua.org/docs/getting-started) ve [kaynak deposu](https://github.com/ClassicMiniDIY/OpenECUAlliance).

Bu belge çevrimiçi kaynak incelemesiyle hazırlanmıştır; lisansların tamamının hukuki uyumu, adapter çalışma zamanı, gerçek motor doğruluğu ve tuning güvenliği test edilmiş değildir.
