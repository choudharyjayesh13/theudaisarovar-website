/*
 * Handpan ambience — a tiny generative handpan player (Web Audio, no audio files).
 * D Kurd scale, soft random-walk melody, bass "ding" on the downbeat, airy reverb.
 * Adds a floating ♪ button; browsers only allow sound after a tap, so it starts on click.
 * The on/off choice is remembered per visitor (localStorage).
 *
 * Usage: <script src="/handpan.js" defer></script>
 * Optional: <script src="/handpan.js" data-position="left" data-color="#d4af37" defer></script>
 */
(function () {
  if (window.__handpan) return;
  window.__handpan = true;

  var script = document.currentScript;
  var POS = (script && script.dataset.position) || "left";
  var COLOR = (script && script.dataset.color) || "#d4af37";
  var KEY = "handpan-on";

  // D Kurd: D3 | A3 Bb3 C4 D4 E4 F4 G4 A4 C5
  var DING = 146.83;
  var NOTES = [220.0, 233.08, 261.63, 293.66, 329.63, 349.23, 392.0, 440.0, 523.25];
  var BPM = 66;
  var STEP = 60 / BPM / 2; // eighth notes

  var ctx, master, reverb, dry, timer, nextTime, step = 0, idx = 3, playing = false;

  function store(v) { try { localStorage.setItem(KEY, v ? "1" : "0"); } catch (e) {} }
  function wanted() { try { return localStorage.getItem(KEY) === "1"; } catch (e) { return false; } }

  function impulse(seconds, decay) {
    var rate = ctx.sampleRate, len = Math.floor(rate * seconds);
    var buf = ctx.createBuffer(2, len, rate);
    for (var c = 0; c < 2; c++) {
      var d = buf.getChannelData(c);
      for (var i = 0; i < len; i++) d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, decay);
    }
    return buf;
  }

  function setup() {
    var AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return false;
    ctx = new AC();
    master = ctx.createGain();
    master.gain.value = 0;
    var comp = ctx.createDynamicsCompressor();
    master.connect(comp).connect(ctx.destination);
    dry = ctx.createGain(); dry.gain.value = 0.75; dry.connect(master);
    reverb = ctx.createConvolver(); reverb.buffer = impulse(3.2, 2.6);
    var wet = ctx.createGain(); wet.gain.value = 0.45;
    reverb.connect(wet).connect(master);
    return true;
  }

  // One handpan strike: fundamental + octave + compound fifth, soft attack, long decay.
  function strike(freq, t, vel) {
    var partials = [[1, 1], [2, 0.32], [3.0, 0.12], [4.02, 0.05]];
    var out = ctx.createGain();
    out.gain.setValueAtTime(0.0001, t);
    out.gain.exponentialRampToValueAtTime(vel, t + 0.012);
    out.gain.exponentialRampToValueAtTime(0.0001, t + 3.6);
    var lp = ctx.createBiquadFilter();
    lp.type = "lowpass";
    lp.frequency.setValueAtTime(4200, t);
    lp.frequency.exponentialRampToValueAtTime(900, t + 1.5);
    out.connect(lp);
    lp.connect(dry);
    lp.connect(reverb);
    partials.forEach(function (p, i) {
      var o = ctx.createOscillator();
      var g = ctx.createGain();
      o.type = "sine";
      o.frequency.value = freq * p[0];
      o.detune.value = (Math.random() - 0.5) * 6;
      g.gain.setValueAtTime(p[1], t);
      // higher partials die faster, like a real tone field
      g.gain.exponentialRampToValueAtTime(0.0001, t + 3.4 / (1 + i * 1.6));
      o.connect(g).connect(out);
      o.start(t);
      o.stop(t + 3.7);
    });
  }

  function pick() {
    var r = Math.random();
    var move = r < 0.35 ? -1 : r < 0.7 ? 1 : r < 0.8 ? -2 : r < 0.9 ? 2 : 0;
    idx = Math.max(0, Math.min(NOTES.length - 1, idx + move));
    return NOTES[idx];
  }

  function schedule() {
    while (nextTime < ctx.currentTime + 0.25) {
      var beat = step % 16;
      if (beat === 0 || (beat === 8 && Math.random() < 0.6)) strike(DING, nextTime, 0.5);
      // phrase-like density: busier mid-bar, rests near the end of the bar
      var p = beat % 4 === 0 ? 0.85 : beat % 2 === 0 ? 0.45 : 0.18;
      if (beat >= 13) p *= 0.4;
      if (Math.random() < p) strike(pick(), nextTime + (Math.random() - 0.5) * 0.02, 0.18 + Math.random() * 0.14);
      if (Math.random() < 0.06) strike(pick() * 2, nextTime + STEP / 2, 0.07); // sparkle
      nextTime += STEP;
      step++;
    }
  }

  function start() {
    if (!ctx && !setup()) return;
    if (ctx.state === "suspended") ctx.resume();
    nextTime = ctx.currentTime + 0.1;
    clearInterval(timer);
    timer = setInterval(schedule, 60);
    master.gain.cancelScheduledValues(ctx.currentTime);
    master.gain.setTargetAtTime(0.55, ctx.currentTime, 0.8);
    playing = true;
    render();
  }

  function stop() {
    if (!ctx) return;
    master.gain.cancelScheduledValues(ctx.currentTime);
    master.gain.setTargetAtTime(0, ctx.currentTime, 0.35);
    setTimeout(function () { if (!playing) clearInterval(timer); }, 1500);
    playing = false;
    render();
  }

  var btn;
  function render() {
    if (!btn) return;
    btn.setAttribute("aria-pressed", playing ? "true" : "false");
    btn.title = playing ? "Pause handpan music" : "Play handpan music";
    btn.innerHTML =
      '<span style="font-size:18px;line-height:1">' + (playing ? "❚❚" : "♪") + "</span>" +
      '<span style="font:600 10px/1 system-ui,sans-serif;letter-spacing:.14em;text-transform:uppercase">' +
      (playing ? "Handpan" : "Play handpan") + "</span>";
    btn.style.boxShadow = playing ? "0 0 0 3px " + COLOR + "33, 0 6px 24px rgba(0,0,0,.35)" : "0 6px 24px rgba(0,0,0,.35)";
  }

  function mount() {
    btn = document.createElement("button");
    btn.type = "button";
    btn.setAttribute("aria-label", "Toggle handpan music");
    var s = btn.style;
    s.position = "fixed";
    s.bottom = "18px";
    s[POS === "right" ? "right" : "left"] = "18px";
    s.zIndex = "2147483000";
    s.display = "flex";
    s.alignItems = "center";
    s.gap = "8px";
    s.padding = "10px 14px";
    s.borderRadius = "999px";
    s.border = "1px solid " + COLOR;
    s.background = "rgba(10,10,10,.82)";
    s.color = COLOR;
    s.cursor = "pointer";
    s.backdropFilter = "blur(6px)";
    s.webkitBackdropFilter = "blur(6px)";
    btn.addEventListener("click", function () {
      if (playing) { stop(); store(false); } else { start(); store(true); }
    });
    document.body.appendChild(btn);
    render();

    // Returning visitors who left it on: resume on their first tap anywhere.
    if (wanted()) {
      var once = function (e) {
        if (e.target === btn || btn.contains(e.target)) return;
        document.removeEventListener("pointerdown", once, true);
        if (!playing) start();
      };
      document.addEventListener("pointerdown", once, true);
    }
    document.addEventListener("visibilitychange", function () {
      if (!ctx) return;
      if (document.hidden) ctx.suspend(); else if (playing) ctx.resume();
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
  else mount();
})();
