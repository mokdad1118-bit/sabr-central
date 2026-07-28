document.getElementById("btnMessage").addEventListener("click", function () {
  fetch("/api/hello")
    .then(response => response.json())
    .then(data => {
      document.getElementById("result").textContent = data.message;
    })
    .catch(error => {
      document.getElementById("result").textContent = "حدث خطأ أثناء جلب الرسالة";
      console.error(error);
    });
});