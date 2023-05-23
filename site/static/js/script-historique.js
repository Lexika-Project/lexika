const urlParam = new URLSearchParams(window.location.search);
const langue = urlParam.get("langue");
const sens = urlParam.get("sens");
const ALLOWED_EXTENTION = ["mp3", "wav"];

presentation = document.querySelector("#presentation");
presentation.innerText = `Historique du sens ${sens} en ${langue}`;

function createTable(json) {
	result = document.querySelector("#resultHistory");
	for (let line of json) {
		let tr = document.createElement("tr");

		// Date
		let td = document.createElement("td");
		const date = new Date(line[0]);
		const hours = String(date.getHours()).padStart(2, "0");
		const min = String(date.getMinutes()).padStart(2, "0");
		const seconde = String(date.getSeconds()).padStart(2, "0");
		td.innerText = `${hours}:${min}:${seconde}, ${date.toLocaleDateString(
			"fr"
		)}`;
		tr.appendChild(td);

		// traduction
		td = document.createElement("td");
		td.innerText = line[1];
		tr.appendChild(td);

		result.appendChild(tr);
	}
}

fetch("/historyRequest", {
	method: "POST",
	headers: {
		Accept: "application/json",
		"Content-Type": "application/json",
	},
	body: JSON.stringify({
		langue: langue,
		sens: sens,
	}),
})
	.then((resp) => {
		return resp.json();
	})
	.then((json) => {
		createTable(json);
	});

const dragBox = document.querySelector(".drag-audio");
dragBox.addEventListener("dragenter", (_) => {
	dragBox.classList.add("drag-audio-enter");
});
dragBox.addEventListener("dragleave", (_) => {
	dragBox.classList.remove("drag-audio-enter");
});

document.addEventListener("dragover", (event) => {
	event.preventDefault();
});
document.addEventListener("drop", (event) => {
	event.preventDefault();
});

const popupError = document.querySelector("#unsupported-extention-popup");
dragBox.addEventListener("drop", (event) => {
	event.preventDefault();
	dragBox.classList.remove("drag-audio-enter");
	const file = event.dataTransfer.files[0];
	const name_split = file.name.split(".");
	const extention = name_split.pop();
	if (ALLOWED_EXTENTION.includes(extention.toLowerCase())) {
		const data = new FormData();
		data.append("file", file);
		data.append("sens", sens);
		data.append("langue", langue);
		console.log(data);
		fetch("/receiveAudio", {
			method: "POST",
			body: data,
		}).then((resp) => {
			console.log(resp);
		});
	} else {
		popupError.innerText = `L'extention ${extention} n'est pas pris en charge.`;
		popupError.hidden = false;
		setTimeout((_) => {
			popupError.hidden = true;
		}, 5000);
	}
});
