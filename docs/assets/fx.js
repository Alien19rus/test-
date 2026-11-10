/* Дополнительные анимации поверх сборки. Всё здесь — отклик на клик или на
   смену состояния: сам по себе в кадре по-прежнему ничего не двигается. */
(() => {
  const reduced = () => matchMedia("(prefers-reduced-motion:reduce)").matches;
  const scene = (sel) => document.querySelector(".office-render " + sel);
  const obj = (id) => scene(`[data-object="${id}"]`);
  const play = (el, frames, opts) => el && el.animate(frames, opts);

  const onClick = {
    // Кот: лапа качается и затухает (заглушили). На третий клик лапа отваливается — см. fx.css.
    cat(res) {
      if (res === "break") return;
      const paw = scene('[data-object="cat"] [data-node-id="1665:2931"]');
      if (!paw) return;
      paw.getAnimations().forEach((a) => a.cancel());
      paw.style.transformOrigin = "30% 95%";
      play(paw, [0, -30, 16, -18, 8, -4, 0].map((d) => ({ rotate: d + "deg" })), { duration: 720, easing: "ease-in-out" });
    },
    // Кружка: глоток — наклон к персонажу; пустая — резкий наклон и встряска.
    cup(res) {
      const cup = obj("cup");
      if (!cup) return;
      cup.style.transformOrigin = "50% 85%";
      if (res === "sip")
        play(cup, [
          { translate: "0 0", rotate: "0deg" },
          { translate: "-4px -9px", rotate: "-24deg", offset: 0.35 },
          { translate: "-4px -9px", rotate: "-30deg", offset: 0.65 },
          { translate: "0 0", rotate: "0deg" },
        ], { duration: 520, easing: "ease-in-out" });
      else if (res === "empty-cup")
        play(cup, [
          { translate: "0 0", rotate: "0deg" },
          { translate: "-5px -11px", rotate: "-48deg", offset: 0.25 },
          { translate: "-3px -11px", rotate: "-40deg", offset: 0.4 },
          { translate: "-6px -11px", rotate: "-50deg", offset: 0.55 },
          { translate: "-3px -11px", rotate: "-42deg", offset: 0.7 },
          { translate: "0 0", rotate: "0deg" },
        ], { duration: 900, easing: "ease-in-out" });
    },
    // Пупырка: продавили пузырь.
    popit() {
      const el = obj("popit");
      if (el) el.style.transformOrigin = "50% 100%";
      play(el, [{ scale: "1 1" }, { scale: "1.14 .78" }, { scale: ".94 1.1" }, { scale: "1 1" }], { duration: 240, easing: "ease-out" });
    },
    // Вилка кондиционера: выдернули — качается на проводе.
    ac(res) {
      if (res !== "success") return;
      const el = obj("ac");
      if (el) el.style.transformOrigin = "50% 0";
      play(el, [0, 11, -8, 5, -3, 0].map((d) => ({ rotate: d + "deg" })), { duration: 900, easing: "ease-out" });
    },
    // Выключатель: лампа гаснет с мерцанием.
    lamp(res) {
      if (res !== "success") return;
      play(document.querySelector(".lamp-shade"), [{ opacity: 0 }, { opacity: 0.3 }, { opacity: 0.05 }, { opacity: 0.25 }, { opacity: 0.2 }], { duration: 420 });
    },
    // Часы: остановили — стрелки дрогнули.
    clock(res) {
      if (res !== "success") return;
      const el = obj("clock");
      play(el, [0, -7, 5, -3, 0].map((d) => ({ rotate: d + "deg" })), { duration: 380, easing: "ease-out" });
    },
  };

  // Общий отклик на клик (ТЗ, раздел 14): высокий предмет качается вбок,
  // висящий на стене — качается на креплении, лежащий — проседает вниз.
  const TILT = new Set(["kettle", "thermometer", "pc", "cat", "radio", "cup", "printer", "belt", "washer"]);
  const SWING = new Set(["plan", "hammer", "clock", "lamp-body", "ac-body", "sticker", "ac"]);
  // массивное и вмурованное (окно, дверь, выключатель) не качается — только чуть подаётся
  const NUDGE = { street: "1px 0", boss: "1px 0", lamp: "0 1px" };
  const bob = (id) => {
    const el = obj(id);
    if (!el) return;
    if (NUDGE[id]) {
      play(el, [{ translate: "0 0" }, { translate: NUDGE[id] }, { translate: "0 0" }], { duration: 140, easing: "ease-out" });
    } else if (SWING.has(id)) {
      el.style.transformOrigin = "50% 0";
      play(el, [0, 5, -3.5, 2, 0].map((d) => ({ rotate: d + "deg" })), { duration: 420, easing: "ease-out" });
    } else if (TILT.has(id)) {
      el.style.transformOrigin = "50% 100%";
      play(el, [
        { rotate: "0deg", translate: "0 0" },
        { rotate: "6deg", translate: "2px 0" },
        { rotate: "-3.5deg", translate: "-1px 0" },
        { rotate: "0deg", translate: "0 0" },
      ], { duration: 320, easing: "ease-out" });
    } else {
      el.style.transformOrigin = "50% 100%";
      play(el, [
        { translate: "0 0", scale: "1 1" },
        { translate: "0 3px", scale: "1.04 .92" },
        { translate: "0 -1px", scale: ".99 1.03" },
        { translate: "0 0", scale: "1 1" },
      ], { duration: 280, easing: "ease-out" });
    }
  };
  // Верный клик по основному источнику: подсветка/индикатор гаснет плавно.
  const MAIN = new Set(["phone", "mobile", "printer", "keyboard", "pc"]);
  const OWN = new Set(["popit"]);

  window.__fx = (id, res, game) => {
    window.__fxGame = game;
    if (reduced()) return;
    // после общего «качка» сборки, чтобы наш отклик был главным
    requestAnimationFrame(() => {
      const own = OWN.has(id) || (id === "cup" && res !== "touch") || (id === "cat" && res === "success");
      if (!own) bob(id);
      if (onClick[id]) onClick[id](res);
      if (MAIN.has(id) && res === "success")
        play(obj(id), [{ filter: "brightness(1.5) saturate(1.4)" }, { filter: "brightness(.92)", offset: 0.6 }, { filter: "brightness(1)" }], { duration: 520, easing: "ease-out" });
      if (game.lastMiss) {
        const who = obj("character");
        play(who, [
          { translate: "0 0", rotate: "0deg" }, { translate: "4px -3px", rotate: "3deg" },
          { translate: "-3px 0", rotate: "-2deg" }, { translate: "2px -1px", rotate: "1deg" }, { translate: "0 0", rotate: "0deg" },
        ], { duration: 300, easing: "ease-out" });
      }
    });
  };

  // Окно находки улетает за кадр перед закрытием.
  window.__eggOut = (done) => {
    const panel = document.querySelector(".egg-overlay .egg-panel");
    let fired = false;
    const finish = () => { if (!fired) { fired = true; done(); } };
    if (!panel || reduced()) return finish();
    const a = panel.animate(
      [{ translate: "0 0", rotate: "0deg" }, { translate: "0 14px", rotate: "2deg", offset: 0.25 }, { translate: "0 -130vh", rotate: "-9deg" }],
      { duration: 360, easing: "cubic-bezier(.5,0,.8,.4)", fill: "forwards" });
    a.onfinish = finish;
    setTimeout(finish, 520);
  };

  // Смена стадии стресса, времени суток и света — по классам комнаты.
  let last = null;
  setInterval(() => {
    const room = document.querySelector(".room");
    if (!room) { last = null; return; }
    const c = room.className;
    const now = {
      mood: (c.match(/mood-(\S+)/) || [])[1],
      period: (c.match(/period-(\d)/) || [])[1],
      dark: c.includes("lamp-is-off"),
      arrival: /(^|\s)arrival(\s|$)/.test(c),
    };
    if (last && !reduced()) {
      const who = obj("character");
      if (now.mood !== last.mood && !now.arrival && now.mood !== "mad") {
        const up = ["Default", "little-stressed", "angry"].indexOf(now.mood) > ["Default", "little-stressed", "angry"].indexOf(last.mood);
        if (who) who.style.transformOrigin = "50% 95%";
        play(who, up
          ? [{ scale: "1 1", rotate: "0deg" }, { scale: "1.09 .94", rotate: "-3deg" }, { scale: ".97 1.05", rotate: "2deg" }, { scale: "1 1", rotate: "0deg" }]
          : [{ scale: "1 1" }, { scale: ".96 1.04" }, { scale: "1 1" }], { duration: up ? 460 : 380, easing: "ease-out" });
        play(document.querySelector(".stress-meter"), [{ scale: 1 }, { scale: up ? 1.12 : 0.94 }, { scale: 1 }], { duration: 380 });
      }
      if (last.dark && !now.dark && now.arrival)
        play(document.querySelector(".lamp-shade"), [{ opacity: 0.2 }, { opacity: 0 }, { opacity: 0.22 }, { opacity: 0.04 }, { opacity: 0.18 }, { opacity: 0 }], { duration: 520 });
    }
    last = now;
  }, 90);

  // Каждый кадр: стрелки часов и шкала стресса идут плавно, без рывков.
  const frame = () => {
    const g = window.__fxGame;
    const shell = document.querySelector(".game-shell");
    if (g && shell) {
      shell.style.setProperty("--clock-minutes", g.clockMinutes);
      shell.style.setProperty("--stress", Math.max(0, Math.min(100, g.stress)).toFixed(2));
    }
    requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);

  // Вход на уровень: ждём, пока сцена полностью дорисуется, показываем тёмный
  // пустой кабинет и только потом пускаем время (персонаж входит, включает свет).
  let heldShell = null;
  const root = document.documentElement;
  setInterval(async () => {
    const shell = document.querySelector(".game-shell");
    if (!shell) { heldShell = null; return; }
    if (shell === heldShell) return;
    heldShell = shell;
    window.__hold = true;
    root.classList.add("fx-hold");
    const imgs = [...shell.querySelectorAll("img")];
    await Promise.race([
      Promise.all(imgs.map((i) => (i.decode ? i.decode().catch(() => {}) : null))),
      new Promise((r) => setTimeout(r, 6000)),
    ]);
    await new Promise((r) => setTimeout(r, 350));
    root.classList.remove("fx-hold");           // кабинет проявляется из темноты
    const intro = window.__fxGame && window.__fxGame.inArrival;
    await new Promise((r) => setTimeout(r, intro ? 1900 : 700)); // пауза в пустом тёмном кабинете
    if (heldShell === shell) window.__hold = false;
  }, 50);
})();
