const value = document.querySelector("#interval_value");
const input = document.querySelector("#interval");
value.textContent = input.value;
input.addEventListener("input", (event) => {
  value.textContent = event.target.value;
});
