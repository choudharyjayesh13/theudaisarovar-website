/* JD Stays & Hospitality — guest gallery & stay planner.
   Content comes from content/explore.json (edited in the admin portal), injected as window.EXPLORE. */
(function () {
  var D = window.EXPLORE, $ = function (s, r) { return (r || document).querySelector(s); };
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var img = function (p) { return (p || '').replace(/^\//, ''); };
  var inr = function (n) { return '₹' + Math.round(n).toLocaleString('en-IN'); };
  var S = { prop: null, tab: 0, occasion: '', inDate: '', outDate: '', adults: 2, kids: 0, stay: -1, meal: 0, exp: {}, fit: '', budget: '' };

  /* ---------- screens & back button ---------- */
  var order = ['intro', 'choose', 'property', 'plan', 'estimate'];
  function show(name, push) {
    document.querySelectorAll('.screen').forEach(function (s) { s.classList.toggle('on', s.id === 's-' + name); });
    document.querySelectorAll('.steps').forEach(function (st) {
      st.innerHTML = [1, 2, 3, 4].map(function (i) { return '<i class="' + (i <= order.indexOf(name) ? 'on' : '') + '"></i>'; }).join('');
    });
    window.scrollTo(0, 0);
    if (push !== false) history.pushState({ s: name }, '', '#' + name);
  }
  window.addEventListener('popstate', function (e) {
    var s = (e.state && e.state.s) || 'intro';
    if ((s === 'property' || s === 'plan' || s === 'estimate') && !S.prop) s = 'choose';
    show(s, false);
  });
  document.addEventListener('click', function (e) { if (e.target.closest('.back')) history.back(); });

  /* ---------- 0. welcome ---------- */
  (function intro() {
    var sc = $('#s-intro'), h = $('.hello'), text = h.dataset.text || h.textContent;
    /* split into whole letters (conjuncts like म्मा stay together) so each lights up on its own */
    var groups = text.split(/(\s+)/).filter(function (w) { return w.length; });   /* whole words: खम्मा, then घणी */
    h.innerHTML = groups.map(function (g) { return /^\s+$/.test(g) ? '<span class="sp" aria-hidden="true"></span>' : '<span class="g">' + esc(g) + '</span>'; }).join('');
    h.setAttribute('aria-label', text);
    var still = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    var at = function (ms, f) { setTimeout(f, still ? 0 : ms); };
    var gs = h.querySelectorAll('.g');
    at(150, function () { sc.classList.add('lit'); });          // lotus glides up from below to the centre and blooms (loading)
    at(3200, function () { sc.classList.add('up'); });          // ...holds, then rises to the top
    at(4400, function () { sc.classList.add('hi'); });          // खम्मा घणी climbs from below
    gs.forEach(function (g, i) {                                 // ...and lights up word by word: खम्मा … घणी
      at(5500 + i * 750, function () { g.classList.add('on'); setTimeout(function () { g.classList.add('done'); }, 420); });
    });
    var end = 5500 + gs.length * 750 + 900;   // short pause, then the rest
    at(end - 700, function () { sc.classList.add('join'); });  // the two words glide together and join
    at(end + 500, function () { sc.classList.add('shine', 'done'); }); // welcome + Enter
  })();
  $('#enter').addEventListener('click', function () { show(S.prop ? 'property' : 'choose'); });

  /* ---------- 1. choose ---------- */
  $('#props').innerHTML = D.properties.map(function (p, i) {
    return '<button class="prop" data-i="' + i + '"><img src="' + esc(img(p.cover)) + '" alt="' + esc(p.name) + '"><span class="cap">' +
      '<span class="label">' + esc(p.location) + '</span><h3>' + esc(p.name) + '</h3><p>' + esc(p.short) + '</p><span class="go">Explore →</span></span></button>';
  }).join('');
  $('#props').addEventListener('click', function (e) {
    var b = e.target.closest('.prop'); if (!b) return;
    var p = D.properties[+b.dataset.i];
    if (S.prop !== p) { S.prop = p; S.tab = 0; S.stay = -1; S.meal = 0; S.exp = {}; }
    renderProperty(); show('property');
  });

  /* ---------- 2. property ---------- */
  function renderProperty() {
    var p = S.prop;
    $('#p-hero').innerHTML = '<img src="' + esc(img(p.cover)) + '" alt="' + esc(p.name) + '"><div class="cap"><span class="label">' + esc(p.location) + '</span><h2>' + esc(p.name) + '</h2><p>' + esc(p.short) + '</p></div>';
    $('#p-intro').textContent = p.intro;
    $('#p-facts').innerHTML = p.facts.map(function (f) { return '<div><b>' + esc(f.number) + '</b><span>' + esc(f.label) + '</span></div>'; }).join('');
    $('#p-tabs').innerHTML = p.galleries.map(function (g, i) { return '<button class="tab' + (i === S.tab ? ' on' : '') + '" data-i="' + i + '">' + esc(g.title) + '</button>'; }).join('');
    renderGallery();
  }
  function renderGallery() {
    var g = S.prop.galleries[S.tab];
    $('#p-gal').innerHTML = g.photos.map(function (ph, i) {
      return '<figure><button data-i="' + i + '" aria-label="Open photo: ' + esc(ph.caption) + '"><img src="' + esc(img(ph.image)) + '" alt="' + esc(ph.caption) + '" loading="lazy"></button><figcaption>' + esc(ph.caption) + '</figcaption></figure>';
    }).join('');
    $('#p-gal').scrollLeft = 0;
    $('#p-count').textContent = g.photos.length + (g.photos.length === 1 ? ' photo' : ' photos · swipe →');
    document.querySelectorAll('#p-tabs .tab').forEach(function (t, i) { t.classList.toggle('on', i === S.tab); });
  }
  $('#p-tabs').addEventListener('click', function (e) {
    var t = e.target.closest('.tab'); if (!t) return;
    S.tab = +t.dataset.i; renderGallery(); t.scrollIntoView({ inline: 'center', block: 'nearest', behavior: 'smooth' });
  });

  /* lightbox */
  var lb = $('#lb'), li = 0;
  function lbShow(i) { var ph = S.prop.galleries[S.tab].photos, n = ph.length; li = (i + n) % n; $('#lb img').src = img(ph[li].image); $('#lb img').alt = ph[li].caption; $('#lb p').textContent = ph[li].caption; }
  $('#p-gal').addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; lbShow(+b.dataset.i); lb.classList.add('on'); });
  $('#lb .x').addEventListener('click', function () { lb.classList.remove('on'); });
  $('#lb .prev').addEventListener('click', function () { lbShow(li - 1); });
  $('#lb .next').addEventListener('click', function () { lbShow(li + 1); });
  var tx = 0; lb.addEventListener('touchstart', function (e) { tx = e.touches[0].clientX; }, { passive: true });
  lb.addEventListener('touchend', function (e) { var d = e.changedTouches[0].clientX - tx; if (Math.abs(d) > 50) lbShow(li + (d < 0 ? 1 : -1)); }, { passive: true });

  $('#to-plan').addEventListener('click', function () { renderPlan(); show('plan'); });

  /* ---------- 3. plan ---------- */
  var iso = function (d) { return new Date(d.getTime() - d.getTimezoneOffset() * 6e4).toISOString().slice(0, 10); };
  function nights() {
    if (!S.inDate || !S.outDate) return 1;
    var n = Math.round((new Date(S.outDate) - new Date(S.inDate)) / 864e5); return n > 0 ? n : 1;
  }
  function priceText(price, unit) {
    if (unit === 'included') return '<strong>Included</strong>';
    if (!price) return '<strong>On request</strong>';
    return '<strong>' + inr(price) + '</strong>' + esc(unit && unit.indexOf('per') === 0 ? unit : 'per ' + (unit || 'night'));
  }
  function incl(x) { var o = S.prop.stay_options[S.stay]; return !!(o && x.included_in && x.included_in.indexOf(o.name) >= 0); }
  function renderPlan() {
    var p = S.prop;
    $('#pl-title').textContent = 'Plan your stay at ' + p.name;
    $('#pl-occ').innerHTML = D.occasions.map(function (o) { return '<button class="chip' + (S.occasion === o ? ' on' : '') + '" data-v="' + esc(o) + '">' + esc(o) + '</button>'; }).join('');
    var din = $('#pl-in'), dout = $('#pl-out'), t = new Date();
    var last = p.valid_until || '', lastIn = last ? iso(new Date(new Date(last).getTime() - 864e5)) : '';
    din.min = iso(t); din.max = lastIn; dout.max = last;
    if (!S.inDate) { var a = new Date(t.getTime() + 7 * 864e5); S.inDate = iso(a); S.outDate = iso(new Date(a.getTime() + 864e5)); }
    if (lastIn && S.inDate > lastIn) { S.inDate = iso(t) > lastIn ? lastIn : iso(t); }
    if (last && S.outDate > last) S.outDate = last;
    if (S.outDate <= S.inDate) S.outDate = iso(new Date(new Date(S.inDate).getTime() + 864e5));
    din.value = S.inDate; dout.value = S.outDate; dout.min = S.inDate;
    $('#pl-valid').textContent = p.package_note || '';
    $('#pl-ad').textContent = S.adults; $('#pl-kd').textContent = S.kids;
    $('#pl-stay').innerHTML = p.stay_options.map(function (o, i) {
      return '<button class="opt' + (S.stay === i ? ' on' : '') + '" data-i="' + i + '"><b>' + esc(o.name) + '</b><span class="pr">' + priceText(o.price, o.unit) + '</span><small>' + esc(o.detail) + '</small>' + (o.includes && o.includes.length ? '<ul class="inc">' + o.includes.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul>' : '') + '</button>';
    }).join('');
    $('#q-meal').style.display = p.meals.length > 1 ? '' : 'none';
    $('#pl-meal').innerHTML = p.meals.map(function (m, i) {
      return '<button class="opt' + (S.meal === i ? ' on' : '') + '" data-i="' + i + '"><b>' + esc(m.name) + '</b><span class="pr">' + (i === 0 && !m.price ? '' : priceText(m.price, 'per room / night')) + '</span></button>';
    }).join('');
    $('#pl-exp').innerHTML = p.experiences.map(function (x, i) {
      var tag = incl(x) || x.unit === 'included' ? ' · included in your package' : (x.price ? ' · ' + inr(x.price) + ' ' + x.unit : ' · on request');
      return '<button class="chip' + (S.exp[i] ? ' on' : '') + '" data-i="' + i + '">' + esc(x.name) + '<span style="color:var(--mute);font-size:.8rem">' + esc(tag) + '</span></button>';
    }).join('');
    checkPlan();
  }
  function checkPlan() { $('#to-est').disabled = S.stay < 0; $('#to-est').textContent = S.stay < 0 ? 'Choose a stay option' : 'See my estimate'; }
  $('#pl-occ').addEventListener('click', function (e) { var c = e.target.closest('.chip'); if (!c) return; S.occasion = S.occasion === c.dataset.v ? '' : c.dataset.v; renderPlan(); });
  $('#pl-in').addEventListener('change', function (e) {
    S.inDate = e.target.value; var o = new Date(S.inDate); o.setDate(o.getDate() + 1);
    if (!S.outDate || S.outDate <= S.inDate) S.outDate = iso(o); renderPlan();
  });
  $('#pl-out').addEventListener('change', function (e) { var mx = S.prop.valid_until; S.outDate = mx && e.target.value > mx ? mx : e.target.value; renderPlan(); });
  document.querySelectorAll('[data-step]').forEach(function (b) {
    b.addEventListener('click', function () {
      var k = b.dataset.step, d = +b.dataset.d; S[k] = Math.max(k === 'adults' ? 1 : 0, Math.min(40, S[k] + d));
      $('#pl-ad').textContent = S.adults; $('#pl-kd').textContent = S.kids;
    });
  });
  $('#pl-stay').addEventListener('click', function (e) { var o = e.target.closest('.opt'); if (!o) return; S.stay = +o.dataset.i; renderPlan(); });
  $('#pl-meal').addEventListener('click', function (e) { var o = e.target.closest('.opt'); if (!o) return; S.meal = +o.dataset.i; renderPlan(); });
  $('#pl-exp').addEventListener('click', function (e) { var c = e.target.closest('.chip'); if (!c) return; var i = +c.dataset.i; if (S.exp[i]) delete S.exp[i]; else S.exp[i] = 1; renderPlan(); });
  $('#to-est').addEventListener('click', function () { if (S.stay < 0) return; renderEstimate(); show('estimate'); });

  /* ---------- 4. estimate ---------- */
  function rooms(o) {
    if (!o.guests) return 1;
    var per = o.guests && o.guests <= 4 ? o.guests : 0;
    return per ? Math.max(1, Math.ceil((S.adults + S.kids * 0.5) / per)) : 1;
  }
  function calc() {
    var p = S.prop, o = p.stay_options[S.stay], n = nights(), r = rooms(o), m = p.meals[S.meal], total = 0, unknown = false, lines = [];
    if (o.price) { total += o.price * n * r; } else unknown = true;
    if (m && m.price && !/all meals/i.test(o.detail)) total += m.price * n * r;
    else if (m && !m.price && S.meal > 0) unknown = true;
    Object.keys(S.exp).forEach(function (i) {
      var x = p.experiences[i]; lines.push(x.name + (incl(x) ? ' (included)' : ''));
      if (x.unit === 'included' || incl(x)) return;
      if (!x.price) { unknown = true; return; }
      total += x.unit === 'per person' ? x.price * (S.adults + S.kids) : /tent/.test(x.unit) ? x.price * r : x.price;
    });
    return { o: o, n: n, r: r, m: m, total: total, unknown: unknown, exps: lines };
  }
  function ref() {
    if (!S.ref) { var d = new Date(); S.ref = 'JD-' + S.prop.id + '-' + ('0' + d.getDate()).slice(-2) + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + Math.floor(100 + Math.random() * 900); }
    return S.ref;
  }
  var fmtD = function (s) { return s ? new Date(s).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : '—'; };
  function renderEstimate() {
    S.ref = null;
    var c = calc(), p = S.prop;
    var guests = S.adults + ' adult' + (S.adults > 1 ? 's' : '') + (S.kids ? ', ' + S.kids + ' child' + (S.kids > 1 ? 'ren' : '') : '');
    var name = (S.occasion ? S.occasion.replace(/ \/.*/, '') + ' at ' : 'Your stay at ') + p.name;
    $('#es-name').textContent = name;
    $('#es-dl').innerHTML =
      '<dt>Dates</dt><dd>' + fmtD(S.inDate) + ' → ' + fmtD(S.outDate) + ' · ' + c.n + ' night' + (c.n > 1 ? 's' : '') + '</dd>' +
      '<dt>Guests</dt><dd>' + esc(guests) + '</dd>' +
      '<dt>Stay</dt><dd>' + esc(c.o.name) + (c.r > 1 ? ' × ' + c.r : '') + '</dd>' +
      '<dt>Meals</dt><dd>' + esc(c.m ? c.m.name : '—') + '</dd>' +
      (c.exps.length ? '<dt>Extras</dt><dd>' + esc(c.exps.join(', ')) + '</dd>' : '');
    $('#es-total').innerHTML = c.total ? '<small>Estimated total</small><b>' + inr(c.total) + (c.unknown ? ' +' : '') + '</b><span>' +
      (c.unknown ? 'Plus items priced on request. ' : '') + 'Before GST · starting rates</span>'
      : '<small>Your estimate</small><b style="font-size:1.8rem">Custom quote</b><span>Our team will share the best price for your dates</span>';
    $('#es-fit').innerHTML = ['Yes, it fits my budget', 'I need something lower', 'I want to upgrade'].map(function (f) { return '<button class="chip' + (S.fit === f ? ' on' : '') + '" data-v="' + f + '">' + f + '</button>'; }).join('');
    $('#es-bud').innerHTML = D.budgets.map(function (b) { return '<button class="chip' + (S.budget === b ? ' on' : '') + '" data-v="' + esc(b) + '">' + esc(b) + '</button>'; }).join('');
    $('#es-ref').textContent = 'Reference ' + ref();
  }
  $('#es-fit').addEventListener('click', function (e) { var c = e.target.closest('.chip'); if (!c) return; S.fit = c.dataset.v; var r = S.ref; renderEstimate(); S.ref = r; $('#es-ref').textContent = 'Reference ' + r; });
  $('#es-bud').addEventListener('click', function (e) { var c = e.target.closest('.chip'); if (!c) return; S.budget = S.budget === c.dataset.v ? '' : c.dataset.v; var r = S.ref; renderEstimate(); S.ref = r; $('#es-ref').textContent = 'Reference ' + r; });

  $('#send').addEventListener('click', function () {
    var c = calc(), p = S.prop, nm = $('#es-guest').value.trim();
    var lines = [
      'Khamma Ghani! 🙏 I\'m interested in staying with JD Stays & Hospitality.',
      '',
      '*Property:* ' + p.name,
      S.occasion ? '*Occasion:* ' + S.occasion : null,
      '*Dates:* ' + fmtD(S.inDate) + ' to ' + fmtD(S.outDate) + ' (' + c.n + ' night' + (c.n > 1 ? 's' : '') + ')',
      '*Guests:* ' + S.adults + ' adults' + (S.kids ? ', ' + S.kids + ' children' : ''),
      '*Stay:* ' + c.o.name + (c.r > 1 ? ' × ' + c.r : ''),
      '*Meals:* ' + (c.m ? c.m.name : '—'),
      c.exps.length ? '*Experiences:* ' + c.exps.join(', ') : null,
      c.total ? '*Website estimate:* ' + inr(c.total) + (c.unknown ? ' + items on request' : '') + ' (before GST)' : '*Estimate:* custom quote',
      S.fit ? '*Budget check:* ' + S.fit : null,
      S.budget ? '*My budget:* ' + S.budget : null,
      nm ? '*Name:* ' + nm : null,
      '',
      'YES, I\'m interested. Please share the final rate.',
      'Ref: ' + ref()
    ].filter(function (l) { return l !== null; }).join('\n');
    var num = String(D.whatsapp_number).replace(/\D/g, ''); if (num.length === 10) num = '91' + num;
    window.location.href = 'https://wa.me/' + num + '?text=' + encodeURIComponent(lines);
  });

  /* open straight on a property: explore.html#UDS or #GH */
  var h = location.hash.slice(1).toUpperCase(), start = D.properties.filter(function (p) { return p.id === h; })[0];
  history.replaceState({ s: 'intro' }, '', location.pathname);
  if (start) { S.prop = start; renderProperty(); }
})();
