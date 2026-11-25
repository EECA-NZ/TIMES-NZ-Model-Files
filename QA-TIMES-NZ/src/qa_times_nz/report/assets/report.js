function updateContents() {
  const page = document.querySelector('.page:not([hidden])');
  const sections = Array.from(page.querySelectorAll('.report-section'));
  if (!sections.length) return;
  const current = sections.find(section => section.getBoundingClientRect().bottom > 132)
    || sections[sections.length - 1];
  page.querySelectorAll('nav a').forEach(link => {
    if (link.hash === '#' + current.id) link.setAttribute('aria-current', 'location');
    else link.removeAttribute('aria-current');
  });
}
const sectionObserver = new IntersectionObserver(updateContents, {
  rootMargin: '-132px 0px 0px 0px'
});
function showPage(requested = location.hash.slice(1)) {
  sectionObserver.disconnect();
  const target = document.getElementById(requested);
  const selected = target?.closest('.page')?.id || 'summary';
  document.querySelectorAll('.page').forEach(page => {page.hidden = page.id !== selected;});
  document.querySelectorAll('nav a[data-page]').forEach(link => {
    if (link.dataset.page === selected) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  });
  requestAnimationFrame(() => {
    if (selected !== 'summary' && requested !== selected)
      document.getElementById(requested).scrollIntoView();
    updateContents();
    document.querySelectorAll('#' + selected + ' .report-section')
      .forEach(section => sectionObserver.observe(section));
  });
}
window.addEventListener('hashchange', () => showPage());
// Some embedded viewers (e.g. Teams preview) never fire hashchange for in-page links.
document.addEventListener('click', event => {
  const link = event.target.closest('nav a[href^="#"]');
  if (!link) return;
  event.preventDefault();
  showPage(link.hash.slice(1));
  try {history.replaceState(null, '', link.hash);} catch (error) {/* URL not writable */}
});
showPage();
