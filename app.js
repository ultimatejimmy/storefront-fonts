document.addEventListener('DOMContentLoaded', () => {
  let allFonts = [];
  let currentCategory = 'all';
  let searchQuery = '';
  let currentSort = 'featured';
  let customSpecimenText = 'The quick brown fox jumps over the lazy dog.';
  let currentFontSize = 22;

  const fontsGrid = document.getElementById('fonts-grid');
  const searchInput = document.getElementById('search-input');
  const sortSelect = document.getElementById('sort-select');
  const specimenInput = document.getElementById('specimen-text-input');
  const fontSizeSlider = document.getElementById('font-size-slider');
  const fontSizeLabel = document.getElementById('font-size-label');
  const presetButtons = document.querySelectorAll('.specimen-preset-btn');
  const categoryButtons = document.querySelectorAll('.category-tags .tag-btn');
  const themeToggleBtn = document.getElementById('theme-toggle-btn');

  // Navigation Links
  const navLinks = document.querySelectorAll('.nav-link');
  const sections = document.querySelectorAll('.section');

  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = link.getAttribute('data-target');
      navLinks.forEach(l => l.classList.remove('active'));
      link.classList.add('active');
      sections.forEach(sec => {
        if (sec.id === targetId) {
          sec.classList.add('active');
        } else {
          sec.classList.remove('active');
        }
      });
    });
  });

  // Theme Toggle
  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'light';
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
    });
  }

  // Specimen Controls
  if (specimenInput) {
    specimenInput.addEventListener('input', (e) => {
      customSpecimenText = e.target.value.trim() || 'The quick brown fox jumps over the lazy dog.';
      presetButtons.forEach(b => b.classList.remove('active'));
      updateAllSpecimens();
    });
  }

  presetButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      presetButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const text = btn.getAttribute('data-text');
      specimenInput.value = text;
      customSpecimenText = text;
      updateAllSpecimens();
    });
  });

  if (fontSizeSlider) {
    fontSizeSlider.addEventListener('input', (e) => {
      currentFontSize = e.target.value;
      if (fontSizeLabel) fontSizeLabel.textContent = `${currentFontSize}px`;
      updateAllSpecimens();
    });
  }

  function updateAllSpecimens() {
    const textEls = document.querySelectorAll('.font-specimen-text');
    textEls.forEach(el => {
      el.textContent = customSpecimenText;
      el.style.fontSize = `${currentFontSize}px`;
    });
  }

  // Categories
  categoryButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      categoryButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentCategory = btn.getAttribute('data-category');
      renderFonts();
    });
  });

  // Search & Sort
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      searchQuery = e.target.value.toLowerCase().trim();
      renderFonts();
    });
  }

  if (sortSelect) {
    sortSelect.addEventListener('change', (e) => {
      currentSort = e.target.value;
      renderFonts();
    });
  }

  // Form Category Pills
  const formCatPills = document.querySelectorAll('#form-category-pills .cat-pill');
  const subCatInput = document.getElementById('sub-category');
  formCatPills.forEach(pill => {
    pill.addEventListener('click', () => {
      formCatPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      if (subCatInput) subCatInput.value = pill.getAttribute('data-value');
    });
  });

  // Submit Form (Metadata Only -> GitHub Issue)
  const submitForm = document.getElementById('font-submit-form');
  if (submitForm) {
    submitForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const fontName = document.getElementById('sub-font-name').value.trim();
      const author = document.getElementById('sub-author').value.trim();
      const sourceUrl = document.getElementById('sub-source-url').value.trim();
      const license = document.getElementById('sub-license').value;
      const licenseUrl = document.getElementById('sub-license-url').value.trim();
      const category = subCatInput ? subCatInput.value : 'Serif';
      const desc = document.getElementById('sub-desc').value.trim();

      const issueTitle = `Font Submission: ${fontName}`;
      const bodyLines = [
        `### Font Submission Request`,
        ``,
        `**Font Family:** ${fontName}`,
        `**Creator / Foundry:** ${author}`,
        `**Category:** ${category}`,
        `**Open License:** ${license}`,
        `**Upstream Source URL:** ${sourceUrl}`,
      ];

      if (licenseUrl) {
        bodyLines.push(`**Upstream License File URL:** ${licenseUrl}`);
      }
      if (desc) {
        bodyLines.push(``, `**Description & E-Ink Notes:**`, desc);
      }

      bodyLines.push(
        ``,
        `---`,
        `*Notice: No font files are uploaded. Maintainers verify licensing directly from the upstream repository.*`,
        `*Submitted via Storefront Fonts Catalog Site*`
      );

      const issueBody = encodeURIComponent(bodyLines.join('\n'));
      const repoUrl = 'https://github.com/ultimatejimmy/storefront-fonts';
      const githubIssueUrl = `${repoUrl}/issues/new?title=${encodeURIComponent(issueTitle)}&labels=font-submission&body=${issueBody}`;

      window.open(githubIssueUrl, '_blank');
    });
  }

  // Load and inject dynamic @font-face rules
  const loadedFontFaces = new Set();
  function loadFontFace(fontFamily, previewUrl) {
    if (!previewUrl || loadedFontFaces.has(fontFamily)) return;

    // Fall back to relative path if viewing locally / before GitHub Pages is live
    let finalUrl = previewUrl;
    if (window.location.hostname !== 'ultimatejimmy.github.io' && previewUrl.includes('/previews/')) {
      const idx = previewUrl.indexOf('previews/');
      if (idx !== -1) {
        finalUrl = './' + previewUrl.slice(idx);
      }
    }

    try {
      const fontFace = new FontFace(fontFamily, `url('${finalUrl}')`, {
        weight: '100 900',
        style: 'normal'
      });
      fontFace.load().then(loaded => {
        document.fonts.add(loaded);
        loadedFontFaces.add(fontFamily);
      }).catch(err => {
        console.warn(`Could not load preview font for ${fontFamily}:`, err);
      });
    } catch (e) {
      console.warn(e);
    }
  }

  // Render Font Cards
  function renderFonts() {
    if (!fontsGrid) return;

    let filtered = allFonts.filter(f => {
      const matchCat = (currentCategory === 'all' || f.category === currentCategory);
      const matchSearch = !searchQuery ||
        f.name.toLowerCase().includes(searchQuery) ||
        (f.author && f.author.toLowerCase().includes(searchQuery)) ||
        (f.description && f.description.toLowerCase().includes(searchQuery));
      return matchCat && matchSearch;
    });

    filtered.sort((a, b) => {
      if (currentSort === 'downloads') return (b.downloads || 0) - (a.downloads || 0);
      if (currentSort === 'likes') return (b.user_thumbs_up || 0) - (a.user_thumbs_up || 0);
      if (currentSort === 'name-asc') return a.name.localeCompare(b.name);
      if (currentSort === 'author-asc') return (a.author || '').localeCompare(b.author || '');
      return (b.stars || 0) - (a.stars || 0);
    });

    if (filtered.length === 0) {
      fontsGrid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 3rem 1rem; color: var(--text-muted);">
          <p style="font-size: 1.1rem; margin-bottom: 0.5rem;">No fonts found matching your search.</p>
          <p style="font-size: 0.85rem;">Try a different keyword or category filter.</p>
        </div>
      `;
      return;
    }

    fontsGrid.innerHTML = filtered.map(font => {
      const customFamily = `Preview_${font.id}`;
      if (font.preview_font_url) {
        loadFontFace(customFamily, font.preview_font_url);
      }

      const safeName = font.name.replace(/'/g, "\\'");
      const licenseShort = font.license.includes('OFL') ? 'OFL 1.1' : (font.license.includes('Apache') ? 'Apache 2.0' : (font.license.includes('MIT') ? 'MIT' : 'Open License'));

      return `
        <article class="font-card">
          <div>
            <div class="font-card-header">
              <div class="font-title-wrap">
                <h2 class="font-title" style="font-family: '${customFamily}', serif;">${escapeHtml(font.name)}</h2>
                <span class="font-author">By ${escapeHtml(font.author || font.owner || 'Open Source')}</span>
              </div>
              <div class="font-meta-badges">
                <span class="font-badge">${escapeHtml(font.category)}</span>
                <span class="font-badge license">${escapeHtml(licenseShort)}</span>
              </div>
            </div>

            <div class="font-specimen-box">
              <div class="font-specimen-text" style="font-family: '${customFamily}', serif; font-size: ${currentFontSize}px;">
                ${escapeHtml(customSpecimenText)}
              </div>
            </div>

            <p class="font-desc">${escapeHtml(font.description || '')}</p>
          </div>

          <div class="font-card-footer">
            <div class="font-stats">
              <span>★ ${font.stars || 0}</span>
              ${font.downloads ? `<span>📥 ${formatNum(font.downloads)}</span>` : ''}
              ${font.user_thumbs_up ? `<span>👍 ${font.user_thumbs_up}</span>` : ''}
            </div>
            <div class="font-actions">
              <a href="${font.download_url}" class="btn-download" title="Download Full Font Family (.zip)">
                <span>📥</span> Full Family
              </a>
              <button type="button" class="btn-suggest" onclick="suggestChange('${safeName}')" title="Suggest metadata update or report issue">
                ✏️
              </button>
            </div>
          </div>
        </article>
      `;
    }).join('');
  }

  window.suggestChange = function(fontName) {
    const issueTitle = `Change Suggestion: ${fontName}`;
    const issueBody = encodeURIComponent([
      `### Font Metadata Correction / Suggestion`,
      ``,
      `**Target Font:** ${fontName}`,
      `**Proposed Changes / Details:**`,
      `[Describe any proposed metadata correction, upstream source update, or licensing note here]`,
      ``,
      `---`,
      `*Submitted via Storefront Fonts Catalog Site*`
    ].join('\n'));
    const url = `https://github.com/ultimatejimmy/storefront-fonts/issues/new?title=${encodeURIComponent(issueTitle)}&labels=suggest-change&body=${issueBody}`;
    window.open(url, '_blank');
  };

  function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function formatNum(n) {
    if (!n) return '0';
    return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : `${n}`;
  }

  // Fetch fonts.json
  fetch('fonts.json')
    .then(res => res.json())
    .then(data => {
      allFonts = data.fonts || [];
      renderFonts();
    })
    .catch(err => {
      console.error('Failed to load fonts.json:', err);
      if (fontsGrid) {
        fontsGrid.innerHTML = `<p style="grid-column: 1 / -1; text-align: center; color: red;">Failed to load font catalog.</p>`;
      }
    });
});
