document.addEventListener('DOMContentLoaded', () => {
function openModal($el, $trigger) {
    $el.classList.add('is-active');
    const dataValue = $trigger.dataset.value;
    if (dataValue) {
        const hiddenInput = document.getElementById('hidden_id');
        if (hiddenInput) {
            hiddenInput.value = dataValue;
        } else {
            console.error("Hidden input element hidden_id not found!");
        }
    }
}
  
  function closeModal($el) {
    $el.classList.remove('is-active');
  }

  function closeAllModals() {
    (document.querySelectorAll('.modal') || []).forEach(($modal) => {
      closeModal($modal);
    });
  }

(document.querySelectorAll('.js-modal-trigger') || []).forEach(($trigger) => {
    const modal = $trigger.dataset.target;
    const $target = document.getElementById(modal);

    $trigger.addEventListener('click', (event) => {
        openModal($target, event.target);
    });

    const notify_modal = document.querySelector('#modal-notification');
    if(notify_modal) openModal(notify_modal.closest('.modal'), $trigger);
});

  (document.querySelectorAll('.modal-background, .modal-close, .modal-card-head .delete, .modal-card-foot .button') || []).forEach(($close) => {
    const $target = $close.closest('.modal');

    $close.addEventListener('click', () => {
      closeModal($target);
    });
  });

  document.addEventListener('keydown', (event) => {
    if(event.key === "Escape") {
      closeAllModals();
    }
  });
});