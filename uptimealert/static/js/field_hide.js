let elements = document.getElementsByClassName('hide_empty')

for (let element of elements) {
    if (element.textContent.trim() !== '') {
        element.classList.remove('is-hidden')
    }
}
