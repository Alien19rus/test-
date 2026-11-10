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
    // Окно: створка захлопнулась.
    street(res) {
      if (res !== "success") return;
      const el = obj("street");
      if (el) el.style.transformOrigin = "0 50%";
      play(el, [{ scale: "1.07 1" }, { scale: ".985 1" }, { scale: "1 1" }], { duration: 300, easing: "ease-out" });
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

  window.__fx = (id, res, game) => {
    window.__fxGame = game;
    if (reduced() || !onClick[id]) return;
    // после общего «качка» сборки, чтобы наш отклик был главным
    requestAnimationFrame(() => onClick[id](res));
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
      if (now.period !== last.period && !now.arrival)
        play(document.querySelector(".office-render"), [{ filter: "brightness(1)" }, { filter: "brightness(.84)" }, { filter: "brightness(1)" }], { duration: 1100, easing: "ease-in-out" });
      if (last.dark && !now.dark && now.arrival)
        play(document.querySelector(".lamp-shade"), [{ opacity: 0.2 }, { opacity: 0 }, { opacity: 0.22 }, { opacity: 0.04 }, { opacity: 0.18 }, { opacity: 0 }], { duration: 520 });
    }
    last = now;
  }, 90);
})();
