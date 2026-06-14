// Универсальный модал
const Modal = {
  open(renderFn) {
    renderFn();
    const ov = document.getElementById('modal-overlay');
    ov.classList.add('open');
    document.body.style.overflow = 'hidden';
    ov.onclick = e => { if (e.target === ov) Modal.close(); };
  },
  close() {
    document.getElementById('modal-overlay').classList.remove('open');
    document.body.style.overflow = '';
  },
};
