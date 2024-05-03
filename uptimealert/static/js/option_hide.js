let port = document.getElementById('port-container');
let schema = document.getElementById('schema-container');
let hostname = document.getElementById('hostname')

function hide(value) {
  if (value === 'port') {
    port.classList.remove('is-hidden');
  } else {
    port.classList.add('is-hidden');
  }

  if (value === 'http') {
    hostname.placeholder='URL';
    hostname.type='link';
    schema.classList.remove('is-hidden');
  } else {
    hostname.placeholder='Hostname';
    hostname.type='text';
    schema.classList.add('is-hidden');
  }
}

window.addEventListener('load', function() {
  let type_input_value = document.getElementById('type').value;
  hide(type_input_value)
})

document.getElementById('type').addEventListener('change', function() {
  hide(this.value)
})
