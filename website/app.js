'use strict';

(() => {
  const shell = document.querySelector('#clock-preview');
  const hour = document.querySelector('#clock-hours');
  const minute = document.querySelector('#clock-minutes');
  const period = document.querySelector('#clock-period');
  let format = '12';
  let oldStamp = '';

  const themeColors = {
    classic: {top:'#1b1b1b', bottom:'#101010', digit:'#dbdcdf', stage:'#050506'},
    ocean: {top:'#1b4567', bottom:'#122d43', digit:'#d5f1ff', stage:'#071a2b'},
    rose: {top:'#683750', bottom:'#402032', digit:'#ffdeee', stage:'#241520'},
    ivory: {top:'#f7ecd9', bottom:'#bcaf9a', digit:'#283347', stage:'#b9c6cf'},
    forest: {top:'#205d4e', bottom:'#123c32', digit:'#d4ffe8', stage:'#09241d'},
    amber: {top:'#79512c', bottom:'#4d301a', digit:'#ffdf9e', stage:'#22160e'},
  };

  function updateClock() {
    const now = new Date();
    const h = now.getHours();
    const m = String(now.getMinutes()).padStart(2,'0');
    const displayedHour = format === '12' ? String(h % 12 || 12) : (format === '24pad' ? String(h).padStart(2,'0') : String(h));
    const displayedPeriod = format === '12' ? (h < 12 ? 'AM' : 'PM') : '';
    const stamp = displayedHour + ':' + m + displayedPeriod;
    if (stamp === oldStamp) return;
    oldStamp = stamp;
    hour.textContent = displayedHour;
    minute.textContent = m;
    period.textContent = displayedPeriod;
    period.hidden = !displayedPeriod;
    shell.querySelector('.clock-numbers').setAttribute('aria-label', 'Local time: ' + displayedHour + ':' + m + (displayedPeriod ? ' ' + displayedPeriod : ''));
    if (document.visibilityState !== 'hidden') {
      shell.classList.remove('clock-updated');
      void shell.offsetWidth;
      shell.classList.add('clock-updated');
    }
  }

  document.querySelectorAll('[data-format]').forEach(button => {
    button.addEventListener('click', () => {
      format = button.dataset.format;
      document.querySelectorAll('[data-format]').forEach(other => {
        const active = other === button;
        other.classList.toggle('is-active', active);
        other.setAttribute('aria-pressed', String(active));
      });
      oldStamp = '';
      updateClock();
    });
  });

  document.querySelectorAll('[data-theme]').forEach(tile => {
    if (!tile.classList.contains('theme-tile')) return;
    tile.addEventListener('click', () => {
      const palette = themeColors[tile.dataset.theme];
      if (!palette) return;
      shell.style.setProperty('--card-top', palette.top);
      shell.style.setProperty('--card-bottom', palette.bottom);
      shell.style.setProperty('--digit-color', palette.digit);
      shell.style.setProperty('--stage-color', palette.stage);
      shell.dataset.theme = tile.dataset.theme;
      document.querySelectorAll('.theme-tile').forEach(other => {
        const active = other === tile;
        other.classList.toggle('is-selected', active);
        other.setAttribute('aria-pressed', String(active));
      });
      if (window.matchMedia('(prefers-reduced-motion: no-preference)').matches) {
        document.querySelector('#clock-preview').scrollIntoView({behavior:'smooth', block:'center'});
      }
    });
  });

  const screenshots = {
    appearance: {src:'appearance-light.png', title:'Appearance', description:'Adjust formats, brightness, animation and the overall clock experience in one place.', alt:'Light native GTK Appearance settings with a flip-clock preview'},
    colors: {src:'appearance-clock-face.png', title:'Clock colors', description:'Choose independent card and numeral colors. A single action restores the classic look.', alt:'GTK Settings showing customizable flip card and digit colors'},
    photos: {src:'appearance-background.png', title:'Photo library', description:'Keep up to twenty personal images. Choose a favorite or let them change automatically.', alt:'GTK settings with a custom photo library and wallpaper options'},
    dark: {src:'appearance-dark.png', title:'Dark mode', description:'The same considered controls in a refined dark appearance.', alt:'Dark native GTK preferences and flip-clock preview'},
    idle: {src:'screensaver-light.png', title:'Idle behavior', description:'Control activation delay and monitors while GNOME handles locking and display power.', alt:'GTK Screensaver settings including idle detection and multiple displays'},
  };

  const shotImage = document.querySelector('#screenshot-image');
  const shotTitle = document.querySelector('#screenshot-title');
  const shotDescription = document.querySelector('#screenshot-description');
  document.querySelectorAll('[data-shot]').forEach(button => {
    button.addEventListener('click', () => {
      const chosen = screenshots[button.dataset.shot];
      if (!chosen) return;
      shotImage.src = './assets/' + chosen.src;
      shotImage.alt = chosen.alt;
      shotTitle.textContent = chosen.title;
      shotDescription.textContent = chosen.description;
      document.querySelectorAll('[data-shot]').forEach(other => {
        const selected = other === button;
        other.classList.toggle('is-active', selected);
        other.setAttribute('aria-pressed', String(selected));
      });
    });
  });

  let toastTimer;
  function toast(text) {
    const el = document.querySelector('#toast');
    el.textContent = text;
    el.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove('show'), 2500);
  }

  document.querySelector('#copy-install').addEventListener('click', async () => {
    const command = document.querySelector('#install-command').textContent;
    try {
      await navigator.clipboard.writeText(command);
      toast('Installation command copied');
    } catch (_) {
      toast('Select the command above to copy it');
    }
  });

  document.querySelector('#year').textContent = String(new Date().getFullYear());
  updateClock();
  setInterval(updateClock, 15000);
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') updateClock();
  });
})();