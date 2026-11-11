document.getElementById("today").textContent = new Intl.DateTimeFormat("kk-KZ", { day: "numeric", month: "long" }).format(new Date());
