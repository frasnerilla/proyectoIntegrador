document.addEventListener("DOMContentLoaded", () => {

  const $ = (id) => document.getElementById(id);

  $("btn").addEventListener("click", async () => {
    $("error").textContent = "";
    $("status").textContent = "";

    const file = $("audio").files[0];
    if (!file) {
      $("error").textContent = "Selecciona un archivo de audio primero.";
      return;
    }

    $("btn").disabled = true;
    $("status").textContent = "Procesando...";

    try {
      const fd = new FormData();
      fd.append("audio", file);

      const res = await fetch("/api/predict", {
        method: "POST",
        body: fd
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Error desconocido");

      $("edad").textContent = data.edad ?? "—";
      $("faltas").textContent = data.faltas ?? "—";
      $("nota").textContent = data.nota ?? "—";
      $("repite").textContent = data.repite ?? "—";
      $("trabaja").textContent = data.trabaja ?? "—";
      $("horas").textContent = data.horas ?? "—";
      $("motivacion").textContent = data.motivacion ?? "—";

      const predBox = $("pred");
      predBox.classList.remove("alta", "baja");

      if (data.prediccion === "alta") {
        predBox.textContent = "ABANDONO: ALTA";
        predBox.classList.add("alta");
      } else {
        predBox.textContent = "ABANDONO: BAJA";
        predBox.classList.add("baja");
      }

      $("status").textContent = "Hecho ✅";

    } catch (e) {
      $("error").textContent = "Error: " + e.message;
    } finally {
      $("btn").disabled = false;
      setTimeout(() => $("status").textContent = "", 2000);
    }
  });

});
