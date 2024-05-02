let port = document.getElementById('port-container');
let hostname = document.getElementById('hostname')
document.getElementById('type').addEventListener('change', function() {
  if (this.value === 'port') {
    port.classList.remove('hidden');
  } else {
    port.classList.add('hidden');
  }

  if (this.value === 'http') {
    hostname.placeholder='URL';
    hostname.type='link'
  } else {
    hostname.placeholder='Hostname';
    hostname.type='text'
  }
});