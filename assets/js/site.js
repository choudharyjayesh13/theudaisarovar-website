/* The Udaisarovar — site behaviour */
(function () {
  var head = document.querySelector('.site-head');

  /* Header turns solid once you scroll past the top of the home hero */
  if (head && head.classList.contains('over')) {
    var onScroll = function () { head.classList.toggle('solid', window.scrollY > 40); };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* Mobile menu */
  var drawer = document.getElementById('drawer');
  var openBtn = document.querySelector('.menu-btn');
  if (drawer && openBtn) {
    var closeBtn = drawer.querySelector('.close');
    var setOpen = function (open) {
      drawer.classList.toggle('open', open);
      openBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
      document.body.style.overflow = open ? 'hidden' : '';
      (open ? closeBtn : openBtn).focus();
    };
    openBtn.addEventListener('click', function () { setOpen(true); });
    closeBtn.addEventListener('click', function () { setOpen(false); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && drawer.classList.contains('open')) setOpen(false); });
  }

  /* Booking form: today / tomorrow by default, check-out always after check-in */
  var f = document.getElementById('jd-book');
  if (f) {
    var iso = function (x) { return new Date(x.getTime() - x.getTimezoneOffset() * 6e4).toISOString().slice(0, 10); };
    var d = new Date(), t = new Date(Date.now() + 864e5);
    f.in.value = iso(d); f.in.min = iso(d); f.out.value = iso(t); f.out.min = iso(t);
    f.in.addEventListener('change', function () {
      var n = new Date(f.in.value); n.setDate(n.getDate() + 1);
      if (f.out.value <= f.in.value) f.out.value = iso(n);
      f.out.min = iso(n);
    });
  }

  /* YouTube: load the player only when tapped */
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('button.yt');
    if (!b || b.querySelector('iframe')) return;
    b.innerHTML = '<iframe src="https://www.youtube-nocookie.com/embed/' + b.dataset.id +
      '?autoplay=1&rel=0&playsinline=1&modestbranding=1" title="YouTube video" allow="autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen></iframe>';
  });

  var still = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Hero film: load assets/video/hero.mp4 and fade it in once it plays (photo shows until then) */
  var hv = document.querySelector('.hero-video');
  if (hv) {
    hv.style.opacity = '0'; hv.style.transition = 'opacity 1.2s ease';
    if (!still && hv.dataset.src) {
      hv.addEventListener('playing', function () { hv.style.opacity = '1'; });
      hv.addEventListener('error', function () { hv.remove(); }, true);
      hv.src = hv.dataset.src;
      var pr = hv.play && hv.play(); if (pr && pr.catch) pr.catch(function () {});
    } else { hv.remove(); }
  }

  /* Reveal: fade, slide-and-turn, and photo unveil as each block scrolls into view */
  var els = document.querySelectorAll('.rv,.rv-l,.rv-r,.rv-zoom');
  if ('IntersectionObserver' in window && !still) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); } });
    }, { rootMargin: '0px 0px -10% 0px' });
    els.forEach(function (el, i) {
      if (el.classList.contains('rv-l') || el.classList.contains('rv-r')) el.style.transitionDelay = ((i % 3) * 0.12) + 's';
      io.observe(el);
    });
  } else { els.forEach(function (el) { el.classList.add('in'); }); }

  /* Count-up numbers */
  document.querySelectorAll('[data-count]').forEach(function (el) {
    if (still || !('IntersectionObserver' in window)) return;
    var end = +el.dataset.count, done = false;
    var o = new IntersectionObserver(function (en) {
      if (!en[0].isIntersecting || done) return; done = true; o.disconnect();
      var t0 = performance.now();
      (function step(t) {
        var k = Math.min(1, (t - t0) / 1600), v = Math.round(end * (1 - Math.pow(1 - k, 3)));
        el.textContent = v.toLocaleString('en-IN'); if (k < 1) requestAnimationFrame(step);
      })(t0);
    });
    o.observe(el);
  });

  /* Scroll-linked motion: hero drift, parallax insets, sideways photo reel */
  if (!still) {
    var heroMedia = document.querySelector('.hero .media'), heroIn = document.querySelector('.hero .in');
    var pars = [].slice.call(document.querySelectorAll('[data-par]'));
    var reels = [].slice.call(document.querySelectorAll('[data-reel]'));
    var ticking = false;
    var frame = function () {
      ticking = false;
      var y = window.scrollY, vh = window.innerHeight;
      if (heroMedia && y < vh * 1.2) {
        heroMedia.style.transform = 'scale(' + (1 + y / vh * 0.12) + ') translateY(' + (y * 0.25) + 'px)';
        heroIn.style.transform = 'translateY(' + (y * -0.18) + 'px)';
        heroIn.style.opacity = Math.max(0, 1 - y / (vh * 0.7));
      }
      pars.forEach(function (el) {
        var r = el.getBoundingClientRect(); if (r.bottom < -200 || r.top > vh + 200) return;
        var d = (r.top + r.height / 2 - vh / 2);
        el.style.transform = 'translateY(' + (d * +el.dataset.par) + 'px)';
      });
      reels.forEach(function (tr) {
        var sec = tr.parentNode.getBoundingClientRect(); if (sec.bottom < 0 || sec.top > vh) return;
        var p = (vh - sec.top) / (vh + sec.height);
        var max = Math.max(0, tr.scrollWidth - window.innerWidth + 40);
        tr.style.transform = 'translateX(' + (-p * max + 20) + 'px)';
      });
    };
    var req = function () { if (!ticking) { ticking = true; requestAnimationFrame(frame); } };
    window.addEventListener('scroll', req, { passive: true });
    window.addEventListener('resize', req);
    frame();
  }

  /* Tonight's direct rate from our booking engine (JD One), shown where [data-t] rows exist */
  var rows = document.querySelectorAll('[data-t]');
  if (rows.length && window.fetch) {
    var URL = 'https://cyimbgjzxxxszjadxpgv.supabase.co/rest/v1/rpc/be_quote',
      KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN5aW1iZ2p6eHh4c3pqYWR4cGd2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQyMTg2MDgsImV4cCI6MjA5OTc5NDYwOH0.R-8de9Ccqui113tBsAvdhHE04LZ6Hlz09bY1vymAcv4';
    var iso2 = function (x) { return new Date(x.getTime() - x.getTimezoneOffset() * 6e4).toISOString().slice(0, 10); };
    fetch(URL, {
      method: 'POST',
      headers: { apikey: KEY, 'Content-Type': 'application/json', 'Content-Profile': 'jdone' },
      body: JSON.stringify({ p_unit_code: 'UDS', p_in: iso2(new Date()), p_out: iso2(new Date(Date.now() + 864e5)), p_adults: 2, p_children: 0, p_rooms: 1 })
    }).then(function (r) { return r.json(); }).then(function (q) {
      (q.types || []).forEach(function (ty) {
        var cp = (ty.plans || []).filter(function (p) { return p.meal_plan === 'CP'; })[0];
        if (!cp) return;
        document.querySelectorAll('[data-t="' + ty.unit_type + '"] .live').forEach(function (el) {
          el.textContent = '₹' + Math.round(cp.room_amount).toLocaleString('en-IN');
          var lbl = el.parentNode.querySelector('.live-l'); if (lbl) lbl.textContent = 'Tonight ';
        });
      });
    }).catch(function () {});
  }
})();
