// FinanceAI — main.js
// Utility ringan untuk interaksi dasar UI

// ── Format angka ke Rupiah ─────────────────────────────────────
function formatRupiah(angka) {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0
  }).format(angka);
}

// ── Flash message sederhana ────────────────────────────────────
function showFlash(pesan, tipe = 'info') {
  const flash = document.createElement('div');
  flash.className = `flash flash-${tipe}`;
  flash.textContent = pesan;
  document.body.appendChild(flash);
  setTimeout(() => flash.remove(), 3500);
}

// ── Staggered card animation saat halaman load ─────────────────
document.addEventListener('DOMContentLoaded', () => {
  const cards = document.querySelectorAll('.card');
  cards.forEach((card, i) => {
    card.style.animationDelay = `${i * 0.06}s`;
  });
});
