/**
 * main.js
 * Controla a transição de overlay e a reprodução de áudio.
 */

const overlay     = document.getElementById('overlay');
const mainContent = document.getElementById('mainContent');
const startBtn    = document.getElementById('startBtn');
const audio       = new Audio('./audio/pra_voce_guardei_o_amor.mp3');

/**
 * Exibe o conteúdo principal com fade-in após a transição do overlay.
 */
function revealContent() {
  overlay.style.opacity = '0';

  setTimeout(() => {
    overlay.style.display = 'none';
    mainContent.style.display = 'grid';

    // Aguarda o próximo frame para acionar o fade-in via CSS
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        mainContent.style.opacity = '1';
      });
    });
  }, 800);
}

startBtn.addEventListener('click', () => {
  audio.play().catch((err) => {
    console.warn('Reprodução de áudio bloqueada ou arquivo não encontrado.', err);
  });

  revealContent();
});
