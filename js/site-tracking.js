/*
 * Sushi Oribe サイト計測(GA4 / Meta ピクセル)
 * 全ページ(英・中・日)で読み込む。GA4 のタグ本体と GTM は各ページの <head> にある。
 *
 * 送るイベント(すべてに site_language = en / zh / ja が付く)
 *   reserve_click         予約ボタン(TableCheck / WhatsApp)  method, cta_location
 *   event_enquiry_click   貸切・イベント問い合わせの WhatsApp     method, cta_location
 *   language_switch       言語切替                                from_language, to_language
 *   menu_course_select    メニューページのランチ/ディナー         course
 *   social_click          Instagram / Facebook / TikTok / Google  platform, cta_location
 *   preorder_click        マグロ予約注文フォーム                  item, cta_location
 *
 * reserve_click と Meta の Schedule / Contact は移行前からあるイベントで、名前と method は変えていない。
 * GA4 のレポートで method 以外の項目を見るには、管理 > カスタム定義 でイベント スコープの
 * カスタムディメンションとして登録する(cta_location, site_language, to_language, course, platform)。
 */
(function () {
  var html = document.documentElement;
  var lang = (html.getAttribute("lang") || "en").slice(0, 2).toLowerCase();

  function send(name, params) {
    params = params || {};
    params.site_language = lang;
    if (window.gtag) window.gtag("event", name, params);
  }

  // トップページの主なセクション(Webflow のクラス名 → 読みやすい名前)
  var SECTION_NAMES = {
    "section-18": "home_hero",
    "section-63": "japan_expo_banner",
    "section-64": "japan_expo_banner",
    "section-20": "home_art_of_omakase",
    "section-21": "home_seasonal_menu",
    "section-8": "home_meet_chef",
    "testimonial-slider-small": "home_reviews"
  };

  function ctaLocation(a) {
    if (a.closest("#oribe-cta-bar")) return "mobile_bottom_bar";
    if (a.closest(".lang-switch")) return "language_switch";
    if (a.closest(".w-nav")) return "header";
    if (a.closest("[class*='footer']")) return "footer";
    var el = a;
    while (el && el !== document.body) {
      if (window.getComputedStyle(el).position === "fixed") return "floating_button";
      el = el.parentElement;
    }
    var section = a.closest("section");
    if (section && section.className) {
      var cls = String(section.className).split(/\s+/)[0];
      return SECTION_NAMES[cls] || "section:" + cls;
    }
    return "body";
  }

  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a");
    if (!a) return;
    var href = a.href || "";
    var loc = ctaLocation(a);

    // 言語切替
    if (a.closest(".lang-switch")) {
      var to = (a.getAttribute("lang") || "").slice(0, 2).toLowerCase();
      if (to && to !== lang) send("language_switch", { from_language: lang, to_language: to });
      return;
    }

    // 予約(TableCheck)
    if (href.indexOf("tablecheck.com") > -1) {
      if (window.fbq) window.fbq("track", "Schedule");
      send("reserve_click", { method: "tablecheck", cta_location: loc });
      return;
    }

    // WhatsApp(貸切・イベントの問い合わせ文面かどうかで分ける)
    if (href.indexOf("wa.me") > -1 || href.indexOf("whatsapp") > -1) {
      if (window.fbq) window.fbq("track", "Contact");
      send("reserve_click", { method: "whatsapp", cta_location: loc });
      if (/private(%20|\s|\+)event/i.test(href)) {
        send("event_enquiry_click", { method: "whatsapp", cta_location: loc });
      }
      return;
    }

    // メニューページのランチ/ディナー切替ボタン
    var raw = a.getAttribute("href") || "";
    if (raw === "#lunch-omakase" || raw === "#dinner-omakase") {
      send("menu_course_select", { course: raw.indexOf("lunch") > -1 ? "lunch" : "dinner" });
      return;
    }

    // マグロの予約注文フォーム
    if (href.indexOf("jemy26tunaorderform") > -1) {
      send("preorder_click", { item: "tuna", cta_location: loc });
      return;
    }

    // SNS・Google
    var platform =
      href.indexOf("instagram.com") > -1 ? "instagram" :
      href.indexOf("facebook.com") > -1 ? "facebook" :
      href.indexOf("tiktok.com") > -1 ? "tiktok" :
      (href.indexOf("share.google") > -1 || href.indexOf("google.com/maps") > -1 || href.indexOf("maps.app.goo.gl") > -1) ? "google" : "";
    if (platform) send("social_click", { platform: platform, cta_location: loc });
  });
})();
