// Compartir la ficha pública: copiar el texto o el enlace, el menú de compartir del sistema y la imagen
// para Instagram (4:5) o TikTok (9:16), que se dibuja aquí mismo con su foto y el QR (sin teléfono).
(() => {
  const box = document.getElementById("share");
  if (!box) return;
  const EN = document.documentElement.lang === "en";
  const url = box.dataset.url, text = box.dataset.text, title = box.dataset.title;
  const msg = document.getElementById("shMsg");
  const say = (s) => { msg.textContent = s; setTimeout(() => { msg.textContent = ""; }, 5000); };
  const AND = window.MascotasPanelAndroid;
  const copy = async (v, ok) => {
    if (AND && AND.copy) { AND.copy(v); say(ok); return; }
    try { await navigator.clipboard.writeText(v); say(ok); }
    catch (e) { window.prompt(EN ? "Copy it:" : "Cópialo:", v); }
  };
  document.getElementById("shCopy").addEventListener("click", () => copy(url, EN ? "Link copied" : "Enlace copiado"));
  const full = text + "\n" + url;
  document.getElementById("shCopyT").addEventListener("click", () => copy(full, EN ? "Text copied: paste it in your post" : "Texto copiado: pégalo en tu post"));
  // Facebook solo pone el enlace: copiamos antes el texto para pegarlo
  const fb = box.querySelector(".s.fb");
  if (fb) fb.addEventListener("click", () => copy(full, EN ? "Text copied: paste it in the Facebook post" : "Texto copiado: pégalo en el post de Facebook"));
  const more = document.getElementById("shMore");
  if (navigator.share || (AND && AND.share)) {
    more.hidden = false;
    more.addEventListener("click", () => {
      if (AND && AND.share) return AND.share(full, title);
      navigator.share({ title, text: text + "\n", url }).catch(() => {});
    });
  }
  // ---- imagen para Instagram / TikTok
  let P = null;
  try { P = box.dataset.poster ? JSON.parse(box.dataset.poster) : null; } catch (e) { P = null; }
  if (!P) return;
  const T = { "Con la cámara del móvil: verás su ficha y cómo avisar": "Use your phone camera: you will see its profile and how to help",
    "ESCANEA EL QR PARA AVISAR": "SCAN THE QR TO LET THEM KNOW", "ESCANÉAME": "SCAN ME", "LLAMA AL": "CALL", "Mi mascota": "My pet",
    "Pregunta por": "Ask for", "RECOMPENSA:": "REWARD:", "🎁 Recompensa:": "🎁 Reward:", "o": "or", "Macho": "Male", "Hembra": "Female" };
  if (!window.t) window.t = (s) => (EN && T[s]) || s;
  window.SP = window.SP || {}; window.SP[P.species] = [P.sp];
  const load = (src) => new Promise((ok, ko) => { const s = document.createElement("script"); s.src = src; s.onload = ok; s.onerror = ko; document.head.appendChild(s); });
  const img = (src) => new Promise((ok, ko) => { const i = new Image(); i.onload = () => ok(i); i.onerror = ko; i.src = src; });
  const b64 = (blob) => new Promise((ok) => { const r = new FileReader(); r.onload = () => ok(String(r.result).split(",")[1]); r.readAsDataURL(blob); });
  async function draw(size) {
    if (!window.Poster) await load("/static/poster.js?v=" + (document.querySelector('script[src*="share.js"]').src.split("v=")[1] || ""));
    const qr = await img(`/qr/${P.code}.png`);
    const qc = document.createElement("canvas"); qc.width = qr.naturalWidth; qc.height = qr.naturalHeight; qc.getContext("2d").drawImage(qr, 0, 0);
    const f = { photo: P.photo, name: P.name, species: P.species, breed: P.breed, sex: P.sex, age: P.age, color: P.color, reward: P.reward };
    return window.Poster.drawPoster(f, qc, { size, heading: P.heading, note: P.note, adopt: P.adopt, showPhone: false });
  }
  box.querySelectorAll("[data-img]").forEach((b) => b.addEventListener("click", async () => {
    const size = b.dataset.img, app = size === "story" ? "TikTok" : "Instagram";
    b.disabled = true;
    try {
      const cv = await draw(size);
      const blob = await new Promise((ok) => cv.toBlob(ok, "image/jpeg", 0.92));
      const name = `${P.name || "mascota"}-${size === "story" ? "tiktok" : "instagram"}.jpg`.replace(/[^\w.-]+/g, "_");
      await copy(full, "");
      if (AND && AND.saveFile) AND.saveFile(await b64(blob), name, "image/jpeg");
      else { const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = name; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 4000); }
      say(EN ? `Image downloaded and text copied. Open ${app}, upload the image and paste the text.` : `Imagen descargada y texto copiado. Abre ${app}, sube la imagen y pega el texto.`);
    } catch (e) { say(EN ? "The image could not be made" : "No se ha podido hacer la imagen"); }
    b.disabled = false;
  }));
})();
